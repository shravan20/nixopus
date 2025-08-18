package queue

import (
	"context"
	"sync"
	"time"

	"github.com/vmihailenco/taskq/v3"
)

var (
	onceQueues sync.Once
	// Queues - Task Pairs
	CreateDeploymentQueue taskq.Queue
	TaskCreateDeployment  *taskq.Task

	HelloWorldQueue taskq.Queue
	TaskHelloWorld  *taskq.Task
)

// SetupQueues registers queues-tasks par with redis and starts consumers.
func SetupQueues() {
	onceQueues.Do(func() {
		// Queue Nanme: Create Deployment
		CreateDeploymentQueue = RegisterQueue(&taskq.QueueOptions{
			Name:                "create-deployment",
			ConsumerIdleTimeout: 10 * time.Minute,
			MinNumWorker:        1,
			MaxNumWorker:        10,
			MaxNumFetcher:       5,
			ReservationSize:     10,
			ReservationTimeout:  10 * time.Second,
			WaitTimeout:         10 * time.Second,
			BufferSize:          100,
		})	
	})
}

func PushTaskToQueue(queue taskq.Queue, task *taskq.Task, ctx context.Context, data interface{}) error {
	return queue.Add(task.WithArgs(ctx, data))
}