package tasks

import (
	"encoding/json"

	"github.com/google/uuid"
	"github.com/raghavyuva/nixopus-api/internal/features/deploy/types"
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

	_, _ = json.MarshalIndent(prepareContextResult, "", "  ")
	return nil
}
