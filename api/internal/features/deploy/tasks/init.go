package tasks

import (
	"context"
	"sync"
	"time"

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
