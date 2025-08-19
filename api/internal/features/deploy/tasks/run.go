package tasks

import (
	"fmt"
	"strings"
	"time"

	"github.com/docker/docker/api/types/container"
	"github.com/docker/docker/api/types/network"
	"github.com/docker/go-connections/nat"
	"github.com/google/uuid"
	"github.com/raghavyuva/nixopus-api/internal/features/deploy/types"
	"github.com/raghavyuva/nixopus-api/internal/features/logger"
	"github.com/raghavyuva/nixopus-api/internal/features/ssh"
	shared_types "github.com/raghavyuva/nixopus-api/internal/types"
)

type AtomicUpdateContainerResult struct {
	ContainerID     string
	ContainerName   string
	ContainerImage  string
	ContainerStatus string
	UpdatedAt       time.Time
}

func (s *TaskService) formatLog(
	applicationID uuid.UUID,
	deploymentID uuid.UUID,
	message string,
	args ...interface{},
) {
	if len(args) > 0 {
		s.Logger.Log(logger.Info, fmt.Sprintf(message, args...), deploymentID.String())
	} else {
		s.Logger.Log(logger.Info, message, deploymentID.String())
	}
}

// sanitizeEnvVars masks sensitive environment variables for logging
func (s *TaskService) sanitizeEnvVars(envVars map[string]string) []string {
	logEnvVars := make([]string, 0, len(envVars))

	for k, v := range envVars {
		if containsSensitiveKeyword(k) {
			logEnvVars = append(logEnvVars, fmt.Sprintf("%s=********", k))
		} else {
			logEnvVars = append(logEnvVars, fmt.Sprintf("%s=%s", k, v))
		}
	}

	return logEnvVars
}

// prepareContainerConfig creates Docker container configuration
func (s *TaskService) prepareContainerConfig(
	imageName string,
	port nat.Port,
	envVars []string,
	applicationID string,
) container.Config {
	return container.Config{
		Image:    imageName,
		Hostname: "nixopus",
		ExposedPorts: nat.PortSet{
			port: struct{}{},
		},
		Env: envVars,
		Labels: map[string]string{
			"com.docker.compose.project": "nixopus",
			"com.docker.compose.version": "0.0.1",
			"com.project.name":           imageName,
			"com.application.id":         applicationID,
		},
	}
}

// prepareHostConfig creates Docker host configuration with port bindings
func (s *TaskService) prepareHostConfig(port nat.Port, availablePort string) container.HostConfig {
	return container.HostConfig{
		NetworkMode: "bridge",
		PortBindings: map[nat.Port][]nat.PortBinding{
			port: {
				{
					HostIP:   "0.0.0.0",
					HostPort: availablePort,
				},
			},
		},
		PublishAllPorts: true,
	}
}

func (s *TaskService) getAvailablePort() (string, error) {
	ssh := ssh.NewSSH()
	client, err := ssh.Connect()
	if err != nil {
		return "", err
	}
	defer client.Close()

	generatePorts := "seq 49152 65535"

	getUsedPorts := "command -v ss >/dev/null 2>&1 && ss -tan | awk '{print $4}' | cut -d':' -f2 | grep '[0-9]\\{1,5\\}' | sort -u || netstat -tan | awk '{print $4}' | grep ':[0-9]' | cut -d':' -f2 | sort -u"

	cmd := fmt.Sprintf("comm -23 <(%s) <(%s) | sort -R | head -n 1 | tr -d '\\n'", generatePorts, getUsedPorts)

	output, err := client.Run(cmd)
	if err != nil {
		return "", fmt.Errorf("failed to find available port: %w", err)
	}

	port := string(output)
	if port == "" {
		return "", fmt.Errorf("no available ports found in range 49152-65535")
	}

	return port, nil
}

// prepareNetworkConfig creates Docker network configuration
func (s *TaskService) prepareNetworkConfig() network.NetworkingConfig {
	return network.NetworkingConfig{
		EndpointsConfig: map[string]*network.EndpointSettings{
			"bridge": {},
		},
	}
}

func (s *TaskService) getRunningContainers(r shared_types.PrepareContextResult) ([]container.Summary, error) {
	all_containers, err := s.DockerRepo.ListAllContainers()
	if err != nil {
		return nil, types.ErrFailedToListContainers
	}

	var currentContainers []container.Summary
	for _, ctr := range all_containers {
		if ctr.Labels["com.application.id"] == r.Application.ID.String() {
			currentContainers = append(currentContainers, ctr)
		}
	}

	s.formatLog(r.Application.ID, r.ApplicationDeployment.ID, "Found %d running containers", len(currentContainers))
	return currentContainers, nil
}

func (s *TaskService) createContainerConfigs(r shared_types.PrepareContextResult) (container.Config, container.HostConfig, network.NetworkingConfig, string) {
	port_str := fmt.Sprintf("%d", r.Application.Port)
	port, _ := nat.NewPort("tcp", port_str)

	var env_vars []string
	for k, v := range GetMapFromString(r.Application.EnvironmentVariables) {
		env_vars = append(env_vars, fmt.Sprintf("%s=%s", k, v))
	}

	logEnvVars := s.sanitizeEnvVars(GetMapFromString(r.Application.EnvironmentVariables))
	s.formatLog(r.Application.ID, r.ApplicationDeployment.ID, types.LogEnvironmentVariables, logEnvVars)
	s.formatLog(r.Application.ID, r.ApplicationDeployment.ID, types.LogContainerExposingPort, port_str)

	container_config := s.prepareContainerConfig(
		fmt.Sprintf("%s:latest", r.Application.Name),
		port,
		env_vars,
		r.Application.ID.String(),
	)

	s.formatLog(r.Application.ID, r.ApplicationDeployment.ID, "Finding available port...")
	availablePort, err := s.getAvailablePort()
	if err != nil {
		errorMsg := fmt.Sprintf("Failed to get available port: %v", err)
		s.formatLog(r.Application.ID, r.ApplicationDeployment.ID, errorMsg)
		return container.Config{}, container.HostConfig{}, network.NetworkingConfig{}, ""
	}
	s.formatLog(r.Application.ID, r.ApplicationDeployment.ID, "Found available port: %s", availablePort)

	host_config := s.prepareHostConfig(port, availablePort)
	network_config := s.prepareNetworkConfig()

	return container_config, host_config, network_config, availablePort
}

// AtomicUpdateContainer performs a zero-downtime update of a running container
func (s *TaskService) AtomicUpdateContainer(r shared_types.PrepareContextResult) (AtomicUpdateContainerResult, error) {
	if r.Application.Name == "" {
		return AtomicUpdateContainerResult{}, types.ErrMissingImageName
	}

	s.Logger.Log(logger.Info, types.LogUpdatingContainer, r.Application.Name)
	s.formatLog(r.Application.ID, r.ApplicationDeployment.ID, types.LogPreparingToUpdateContainer, r.Application.Name)

	s.formatLog(r.Application.ID, r.ApplicationDeployment.ID, "Checking for running containers...")
	currentContainers, err := s.getRunningContainers(r)
	if err != nil {
		return AtomicUpdateContainerResult{}, err
	}

	s.formatLog(r.Application.ID, r.ApplicationDeployment.ID, "Preparing container configurations...")
	container_config, host_config, network_config, availablePort := s.createContainerConfigs(r)
	if availablePort == "" {
		s.formatLog(r.Application.ID, r.ApplicationDeployment.ID, "Failed to get available port")
		return AtomicUpdateContainerResult{}, types.ErrFailedToGetAvailablePort
	}
	s.formatLog(r.Application.ID, r.ApplicationDeployment.ID, "Container configurations prepared successfully")

	s.formatLog(r.Application.ID, r.ApplicationDeployment.ID, types.LogCreatingNewContainer)
	resp, err := s.DockerRepo.CreateContainer(container_config, host_config, network_config, "")
	if err != nil {
		errorMsg := fmt.Sprintf("Failed to create container: %v", err)
		s.formatLog(r.Application.ID, r.ApplicationDeployment.ID, errorMsg)
		return AtomicUpdateContainerResult{}, types.ErrFailedToCreateContainer
	}
	s.formatLog(r.Application.ID, r.ApplicationDeployment.ID, types.LogNewContainerCreated+"%s", resp.ID)

	if len(currentContainers) > 0 {
		s.formatLog(r.Application.ID, r.ApplicationDeployment.ID, "Stopping %d existing containers...", len(currentContainers))
		for _, ctr := range currentContainers {
			s.formatLog(r.Application.ID, r.ApplicationDeployment.ID, types.LogStoppingOldContainer+"%s", ctr.ID)
			err = s.DockerRepo.StopContainer(ctr.ID, container.StopOptions{Timeout: intPtr(10)})
			if err != nil {
				s.formatLog(r.Application.ID, r.ApplicationDeployment.ID, types.LogFailedToStopOldContainer, err.Error())
			} else {
				s.formatLog(r.Application.ID, r.ApplicationDeployment.ID, "Successfully stopped container: %s", ctr.ID)
			}
		}
		s.formatLog(r.Application.ID, r.ApplicationDeployment.ID, "All existing containers stopped")
	} else {
		s.formatLog(r.Application.ID, r.ApplicationDeployment.ID, "No existing containers found to stop")
	}

	s.formatLog(r.Application.ID, r.ApplicationDeployment.ID, types.LogStartingNewContainer)
	err = s.DockerRepo.StartContainer(resp.ID, container.StartOptions{})
	if err != nil {
		errorMsg := fmt.Sprintf("Failed to start container: %v", err)
		s.formatLog(r.Application.ID, r.ApplicationDeployment.ID, errorMsg)
		s.formatLog(r.Application.ID, r.ApplicationDeployment.ID, "Cleaning up failed container...")
		s.DockerRepo.RemoveContainer(resp.ID, container.RemoveOptions{Force: true})
		return AtomicUpdateContainerResult{}, types.ErrFailedToStartNewContainer
	}
	s.formatLog(r.Application.ID, r.ApplicationDeployment.ID, types.LogNewContainerStartedSuccessfully)

	s.formatLog(r.Application.ID, r.ApplicationDeployment.ID, "Waiting for container to stabilize...")
	time.Sleep(time.Second * 5)

	s.formatLog(r.Application.ID, r.ApplicationDeployment.ID, "Verifying container health...")
	containerInfo, err := s.DockerRepo.GetContainerById(resp.ID)
	if err != nil {
		errorMsg := fmt.Sprintf("Failed to get container info: %v", err)
		s.formatLog(r.Application.ID, r.ApplicationDeployment.ID, errorMsg)
		s.formatLog(r.Application.ID, r.ApplicationDeployment.ID, "Cleaning up failed container...")
		s.DockerRepo.StopContainer(resp.ID, container.StopOptions{})
		s.DockerRepo.RemoveContainer(resp.ID, container.RemoveOptions{Force: true})
		return AtomicUpdateContainerResult{}, types.ErrFailedToUpdateContainer
	}

	if containerInfo.State.Status != "running" {
		errorMsg := fmt.Sprintf("Container is not running, status: %s", containerInfo.State.Status)
		s.formatLog(r.Application.ID, r.ApplicationDeployment.ID, errorMsg)
		s.formatLog(r.Application.ID, r.ApplicationDeployment.ID, "Cleaning up failed container...")
		s.DockerRepo.StopContainer(resp.ID, container.StopOptions{})
		s.DockerRepo.RemoveContainer(resp.ID, container.RemoveOptions{Force: true})
		return AtomicUpdateContainerResult{}, types.ErrFailedToUpdateContainer
	}

	s.formatLog(r.Application.ID, r.ApplicationDeployment.ID, "Container health verification successful")
	s.formatLog(r.Application.ID, r.ApplicationDeployment.ID, "Container update completed successfully")

	return AtomicUpdateContainerResult{
		ContainerID:     resp.ID,
		ContainerName:   containerInfo.Name,
		ContainerImage:  containerInfo.Image,
		ContainerStatus: containerInfo.State.Status,
		UpdatedAt:       time.Now(),
	}, nil
}

// Helper function to create a pointer to an integer
func intPtr(i int) *int {
	return &i
}

// containsSensitiveKeyword checks if a key likely contains sensitive information
func containsSensitiveKeyword(key string) bool {
	sensitiveKeywords := []string{
		"password", "secret", "token", "key", "auth", "credential", "private",
	}

	lowerKey := strings.ToLower(key)
	for _, word := range sensitiveKeywords {
		if strings.Contains(lowerKey, word) {
			return true
		}
	}

	return false
}
