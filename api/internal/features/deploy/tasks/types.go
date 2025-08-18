package tasks

import (
	"context"
	"encoding/json"
	"time"

	"github.com/google/uuid"
	"github.com/raghavyuva/nixopus-api/internal/features/deploy/docker"
	"github.com/raghavyuva/nixopus-api/internal/features/deploy/storage"
	github_service "github.com/raghavyuva/nixopus-api/internal/features/github-connector/service"
	"github.com/raghavyuva/nixopus-api/internal/features/logger"
)

type Type string

const (
	TaskTypeCreateDeploy Type = "create_deploy"
	TaskTypeDeleteDeploy Type = "delete_deploy"
	TaskTypeUpdateDeploy Type = "update_deploy"
	TaskTypeReDeploy     Type = "redeploy"
	TaskTypeRollback     Type = "rollback_deploy"
	TaskTypeRestart      Type = "restart_deploy"
)

type TaskPayload struct {
	ID             string          `json:"id"`
	Data           json.RawMessage `json:"data"`
	RetryCount     int             `json:"retry_count"`
	CreatedAt      time.Time       `json:"created_at"`
	UpdatedAt      time.Time       `json:"updated_at"`
	Status         string          `json:"status"`
	Type           Type            `json:"type"`
	Ctx            context.Context
	UserId         uuid.UUID
	OrganizationId uuid.UUID
}

type TaskRepository interface {
	GetTaskName() string
	GetStatus() string
	Execute() error
}

type TaskService struct {
	Storage        storage.DeployRepository
	Logger         logger.Logger
	DockerRepo     docker.DockerRepository
	Github_service *github_service.GithubConnectorService
}

func NewTaskService(storage storage.DeployRepository, logger logger.Logger, dockerRepo docker.DockerRepository, githubService *github_service.GithubConnectorService) *TaskService {
	return &TaskService{
		Storage:        storage,
		Logger:         logger,
		DockerRepo:     dockerRepo,
		Github_service: githubService,
	}
}

// // TODO:
// Click Create Deploy =>
// 1. Data validated
// 2. Prepare the context/data
// 3. Validate data/contextcon4teCteate a tasktext
// 4. Create a task; push this Queue
// 5. return response

// Worker flow:
// 5. Worker pckups up message
// 	0. Prepare data required all steps x=[]
// 	1. x=[]
// 	2. building the application
// 	3. deploying the application
// 	4. setting up the proxy
// 	5. cleaning up the resources
