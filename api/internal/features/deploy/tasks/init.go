package tasks

import (
	"context"
	"fmt"
	"sync"
	"time"

	"github.com/google/uuid"
	"github.com/raghavyuva/nixopus-api/internal/features/deploy/types"
	"github.com/raghavyuva/nixopus-api/internal/queue"
	shared_types "github.com/raghavyuva/nixopus-api/internal/types"
	"github.com/vmihailenco/taskq/v3"
)

var (
	onceQueues            sync.Once
	CreateDeploymentQueue taskq.Queue
	TaskCreateDeployment  *taskq.Task
)

func (t *TaskService) SetupCreateDeploymentQueue() {
	onceQueues.Do(func() {
		CreateDeploymentQueue = queue.RegisterQueue(&taskq.QueueOptions{
			Name:                "create-deployment",
			ConsumerIdleTimeout: 10 * time.Minute,
			MinNumWorker:        1,
			MaxNumWorker:        10,
			// MaxNumFetcher:       5,
			ReservationSize:    10,
			ReservationTimeout: 10 * time.Second,
			WaitTimeout:        5 * time.Second,
			BufferSize:         100,
		})

		TaskCreateDeployment = taskq.RegisterTask(&taskq.TaskOptions{
			Name: "task_create_deployment",
			Handler: func(ctx context.Context, data shared_types.PrepareContextResult) error {
				t.HandleCreateDeployment(ctx, data)
				return nil
			},
		})
	})

}

func (t *TaskService) StartConsumers(ctx context.Context) error {
	return queue.StartConsumers(ctx)
}

func (t *TaskService) CreateDeploymentTask(deployment *types.CreateDeploymentRequest, userID uuid.UUID, organizationID uuid.UUID) (shared_types.Application, error) {
	prepareContextTask := PrepareContextTask{
		TaskService: t,
		PrepareContextConfig: PrepareContextConfig{
			Deployment: deployment,
		},
		UserId:         userID,
		OrganizationId: organizationID,
	}

	prepareContextResult, err := prepareContextTask.PrepareContext()
	if err != nil {
		return shared_types.Application{}, err
	}

	err = CreateDeploymentQueue.Add(TaskCreateDeployment.WithArgs(context.Background(), prepareContextResult))
	if err != nil {
		fmt.Printf("error enqueuing create deployment: %v\n", err)
	}

	return prepareContextResult.Application, nil
}

func (t *TaskService) HandleCreateDeployment(ctx context.Context, prepareContextResult shared_types.PrepareContextResult) error {
	taskCtx := t.NewTaskContext(prepareContextResult)

	taskCtx.LogAndUpdateStatus("Starting deployment process", shared_types.Cloning)

	repoPath, err := t.Clone(CloneConfig{
		PrepareContextResult: prepareContextResult,
		DeploymentType:       string(shared_types.DeploymentTypeCreate),
		TaskContext:          taskCtx,
	})
	if err != nil {
		taskCtx.LogAndUpdateStatus("Failed to clone repository: "+err.Error(), shared_types.Failed)
		return err
	}

	taskCtx.LogAndUpdateStatus("Repository cloned successfully", shared_types.Building)
	taskCtx.AddLog("Building image from Dockerfile " + repoPath + " for application " + prepareContextResult.Application.Name)
	buildImageResult, err := t.BuildImage(BuildConfig{
		PrepareContextResult: prepareContextResult,
		ContextPath:          repoPath,
		Force:                false,
		ForceWithoutCache:    false,
		TaskContext:          taskCtx,
	})
	if err != nil {
		taskCtx.LogAndUpdateStatus("Failed to build image: "+err.Error(), shared_types.Failed)
		return err
	}

	taskCtx.AddLog("Image built successfully: " + buildImageResult + " for application " + prepareContextResult.Application.Name)
	taskCtx.UpdateStatus(shared_types.Deploying)

	containerResult, err := t.AtomicUpdateContainer(prepareContextResult, taskCtx)
	if err != nil {
		taskCtx.LogAndUpdateStatus("Failed to update container: "+err.Error(), shared_types.Failed)
		return err
	}

	taskCtx.AddLog("Container updated successfully for application " + prepareContextResult.Application.Name + " with container id " + containerResult.ContainerID)
	taskCtx.LogAndUpdateStatus("Deployment completed successfully", shared_types.Deployed)

	return nil
}