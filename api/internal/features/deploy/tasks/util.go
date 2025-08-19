package tasks

import (
	"strings"
	"time"

	"github.com/google/uuid"
	"github.com/raghavyuva/nixopus-api/internal/features/logger"
	shared_types "github.com/raghavyuva/nixopus-api/internal/types"
)

func GetStringFromMap(m map[string]string) string {
	var result string
	for key, value := range m {
		result += key + "=" + value + " "
	}
	return result
}

func GetMapFromString(s string) map[string]string {
	result := make(map[string]string)
	pairs := strings.Split(s, " ")
	for _, pair := range pairs {
		if pair != "" {
			kv := strings.Split(pair, "=")
			if len(kv) == 2 {
				result[kv[0]] = kv[1]
			}
		}
	}
	return result
}			

func (s *TaskService) UpdateDeployment(deployment *shared_types.ApplicationDeployment) {
	err := s.Storage.UpdateApplicationDeployment(deployment)
	if err != nil {
		s.Logger.Log(logger.Error, "Failed to update application deployment: "+err.Error(), "")
	}
}

// updateStatus updates the application status
func (s *TaskService) UpdateStatus(deploymentID uuid.UUID, status shared_types.Status, id uuid.UUID) {
	appStatus := shared_types.ApplicationDeploymentStatus{
		ID:                      id,
		ApplicationDeploymentID: deploymentID,
		Status:                  status,
		UpdatedAt:               time.Now(),
	}

	err := s.Storage.UpdateApplicationDeploymentStatus(&appStatus)
	if err != nil {
		s.Logger.Log(logger.Error, "Failed to update application deployment status: "+err.Error(), "")
	}
}

// addLog adds a new log entry for the application
func (s *TaskService) AddLog(applicationID uuid.UUID, logMessage string, deploymentID uuid.UUID) {
	appLog := shared_types.ApplicationLogs{
		ID:                      uuid.New(),
		ApplicationID:           applicationID,
		Log:                     logMessage,
		CreatedAt:               time.Now(),
		UpdatedAt:               time.Now(),
		ApplicationDeploymentID: deploymentID,
	}

	err := s.Storage.AddApplicationLogs(&appLog)
	if err != nil {
		s.Logger.Log(logger.Error, "Failed to add application log: "+err.Error(), "")
	}
}	