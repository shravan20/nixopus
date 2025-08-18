package tasks

import (
	"context"
	"fmt"

	"github.com/google/uuid"
	"github.com/raghavyuva/nixopus-api/internal/features/deploy/types"
	"github.com/raghavyuva/nixopus-api/internal/queue"
	shared_types "github.com/raghavyuva/nixopus-api/internal/types"
	"github.com/vmihailenco/taskq/v3"
)

func (t *TaskService) CreateDeploymentTask(deployment *types.CreateDeploymentRequest, userID uuid.UUID, organizationID uuid.UUID) error {
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
		return err
	}

	go func() {
		queue.TaskCreateDeployment = taskq.RegisterTask(CreateDeploymentTaskOptions(t))
		err = queue.PushTaskToQueue(queue.CreateDeploymentQueue, queue.TaskCreateDeployment, context.Background(), prepareContextResult)
		if err != nil {
			fmt.Printf("error enqueuing create deployment: %v\n", err)
		}
	}()

	return nil
}

func (t *TaskService) HandleCreateDeployment(ctx context.Context, prepareContextResult shared_types.PrepareContextResult) error {
	fmt.Printf("prepareContextResult: %+v\n", prepareContextResult)
	repoPath, err := t.Clone(CloneConfig{
		PrepareContextResult: prepareContextResult,
		DeploymentType:       string(shared_types.DeploymentTypeCreate),
	})
	fmt.Printf("repoPath: %+v\n", repoPath)
	if err != nil {
		return err
	}

	buildImageResult, err := t.BuildImage(BuildConfig{
		PrepareContextResult: prepareContextResult,
		ContextPath:          repoPath,
		Force:                false,
		ForceWithoutCache:    false,
	})
	fmt.Printf("buildImageResult: %+v\n", buildImageResult)
	containerResult, err := t.AtomicUpdateContainer(prepareContextResult)
	fmt.Printf("containerResult: %+v\n", containerResult)
	if err != nil {
		return err
	}

	return nil
}

// TODO :
// PRE RUN POST RUN COMMANDS EXECUTION
// REVERSE PROXY CONFIGURATION
// Updating the application deployment data and application data found out during the different stages of the tasks
// Logger of the tasks (add log function to the task service)
// Update the statuses during the different stages of the tasks

func CreateDeploymentTaskOptions(t *TaskService) *taskq.TaskOptions {
	return &taskq.TaskOptions{
		Name: "task_create_deployment",
		Handler: t.HandleCreateDeployment,
	}
}