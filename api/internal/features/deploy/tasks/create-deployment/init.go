package createdeployment

import (
	"encoding/json"

	"github.com/google/uuid"
	"github.com/raghavyuva/nixopus-api/internal/features/deploy/tasks"
	"github.com/raghavyuva/nixopus-api/internal/features/deploy/types"
	shared_types "github.com/raghavyuva/nixopus-api/internal/types"
)

type CreateDeploymentTask struct {
	TaskService        *tasks.TaskService
	CreateDeployConfig CreateDeployConfig
	UserId             uuid.UUID
	OrganizationId     uuid.UUID
}

type CreateDeployConfig struct {
	Deployment       *types.CreateDeploymentRequest
	ContextPath      string
	DeploymentConfig *shared_types.ApplicationDeployment
}

func (t *CreateDeploymentTask) GetTaskName() string {
	return string(tasks.TaskTypeCreateDeploy)
}

func (t *CreateDeploymentTask) GetStatus() string {
	return ""
}

type PrepareContextResult struct {
	Application           shared_types.Application
	ApplicationDeployment shared_types.ApplicationDeployment
}

func (t *CreateDeploymentTask) Execute(deployment *types.CreateDeploymentRequest, userID uuid.UUID, organizationID uuid.UUID) error {

	prepareContextResult, err := t.PrepareContext()
	if err != nil {
		return err
	}

	_, _ = json.MarshalIndent(prepareContextResult, "", "  ")
	return nil
}	
