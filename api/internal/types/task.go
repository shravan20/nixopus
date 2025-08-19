package types

type TaskPayload struct {
	Application           Application
	ApplicationDeployment ApplicationDeployment
	Status                *ApplicationDeploymentStatus
}
