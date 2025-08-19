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
	onceQueues sync.Once
	// Queues - Task Pairs
	CreateDeploymentQueue taskq.Queue
	TaskCreateDeployment  *taskq.Task
)

// SetupQueues registers queues-tasks par with redis and starts consumers.
func (t *TaskService) SetupCreateDeploymentQueue() {
	onceQueues.Do(func() {
		// Queue Nanme: Create Deployment
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

		// Task for Create Deployment queue name
		TaskCreateDeployment = taskq.RegisterTask(&taskq.TaskOptions{
			Name: "task_create_deployment",
			Handler: func(ctx context.Context, data shared_types.PrepareContextResult) error {
				fmt.Printf("handler called : %+v\n", data)
				t.HandleCreateDeployment(ctx, data)
				return nil
			},
		})
	})

}

func (t *TaskService) StartConsumers(ctx context.Context) error {
	return queue.StartConsumers(ctx)
}

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

	err = CreateDeploymentQueue.Add(TaskCreateDeployment.WithArgs(context.Background(), prepareContextResult))
	if err != nil {
		fmt.Printf("error enqueuing create deployment: %v\n", err)
	}

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
