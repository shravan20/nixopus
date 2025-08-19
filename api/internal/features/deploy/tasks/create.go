package tasks

import (
	"context"
	"fmt"

	"github.com/google/uuid"
	"github.com/raghavyuva/nixopus-api/internal/features/deploy/types"
	shared_types "github.com/raghavyuva/nixopus-api/internal/types"
)

func (t *TaskService) CreateDeploymentTask(deployment *types.CreateDeploymentRequest, userID uuid.UUID, organizationID uuid.UUID) (shared_types.Application, error) {
	contextTask := ContextTask{
		TaskService: t,
		ContextConfig: ContextConfig{
			Deployment: deployment,
		},
		UserId:         userID,
		OrganizationId: organizationID,
	}

	TaskPayload, err := contextTask.PrepareCreateDeploymentContext()
	if err != nil {
		return shared_types.Application{}, err
	}

	err = CreateDeploymentQueue.Add(TaskCreateDeployment.WithArgs(context.Background(), TaskPayload))
	if err != nil {
		fmt.Printf("error enqueuing create deployment: %v\n", err)
	}

	return TaskPayload.Application, nil
}

func (t *TaskService) HandleCreateDockerfileDeployment(ctx context.Context, TaskPayload shared_types.TaskPayload) error {
	taskCtx := t.NewTaskContext(TaskPayload)

	taskCtx.LogAndUpdateStatus("Starting deployment process", shared_types.Cloning)

	repoPath, err := t.Clone(CloneConfig{
		TaskPayload:    TaskPayload,
		DeploymentType: string(shared_types.DeploymentTypeCreate),
		TaskContext:    taskCtx,
	})
	if err != nil {
		taskCtx.LogAndUpdateStatus("Failed to clone repository: "+err.Error(), shared_types.Failed)
		return err
	}

	taskCtx.LogAndUpdateStatus("Repository cloned successfully", shared_types.Building)
	taskCtx.AddLog("Building image from Dockerfile " + repoPath + " for application " + TaskPayload.Application.Name)
	buildImageResult, err := t.BuildImage(BuildConfig{
		TaskPayload:       TaskPayload,
		ContextPath:       repoPath,
		Force:             false,
		ForceWithoutCache: false,
		TaskContext:       taskCtx,
	})
	if err != nil {
		taskCtx.LogAndUpdateStatus("Failed to build image: "+err.Error(), shared_types.Failed)
		return err
	}

	taskCtx.AddLog("Image built successfully: " + buildImageResult + " for application " + TaskPayload.Application.Name)
	taskCtx.UpdateStatus(shared_types.Deploying)

	containerResult, err := t.AtomicUpdateContainer(TaskPayload, taskCtx)
	if err != nil {
		taskCtx.LogAndUpdateStatus("Failed to update container: "+err.Error(), shared_types.Failed)
		return err
	}

	taskCtx.AddLog("Container updated successfully for application " + TaskPayload.Application.Name + " with container id " + containerResult.ContainerID)
	taskCtx.LogAndUpdateStatus("Deployment completed successfully", shared_types.Deployed)

	return nil
}

// TODO : Implement the docker compose deployment
func (t *TaskService) HandleCreateDockerComposeDeployment(ctx context.Context, TaskPayload shared_types.TaskPayload) error {
	return nil
}

// TODO : Implement the static deployment
func (t *TaskService) HandleCreateStaticDeployment(ctx context.Context, TaskPayload shared_types.TaskPayload) error {
	return nil
}

// TODOD: Shravan implement types and get back
func (t *TaskService) ReDeployApplication(ctx context.Context, request *types.ReDeployApplicationRequest, userID uuid.UUID, organizationID uuid.UUID) (shared_types.Application, error) {

	contextTask := ContextTask{
		TaskService:    t,
		ContextConfig:  request,
		UserId:         userID,
		OrganizationId: organizationID,
	}

	// Prepare the context for re-deployment
	// deployment_details from db
	// application_details from db
	// deploy_status
	// db call to update status
	// prepareDeploymentConfig (app_details, userId, deploymentRestartType.restart, false, false)
	// createAndPrepareDeployment(application, DeploymentRequestConfig)
	// deployRequest, deploySTatus, deploymentConfig
	// push it to Queue

	TaskPayload, err := contextTask.PrepareReDeploymentContext()

	if err != nil {
		return shared_types.Application{}, err
	}
	fmt.Print("Re-deploying application with payload: ", TaskPayload)
	return shared_types.Application{}, nil
}
