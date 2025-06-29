package controller

import (
	"net/http"

	"github.com/go-fuego/fuego"
	"github.com/raghavyuva/nixopus-api/internal/features/domain/types"
	"github.com/raghavyuva/nixopus-api/internal/features/logger"
	shared_types "github.com/raghavyuva/nixopus-api/internal/types"
)

func (c *DomainsController) DeleteDomain(f fuego.ContextWithBody[types.DeleteDomainRequest]) (*shared_types.Response, error) {
	domainRequest, err := f.Body()

	if err != nil {
		return nil, fuego.HTTPError{
			Err:    err,
			Status: http.StatusBadRequest,
		}
	}

	w, r := f.Response(), f.Request()

	if !c.parseAndValidate(w, r, &domainRequest) {
		return nil, fuego.HTTPError{
			Err:    nil,
			Status: http.StatusBadRequest,
		}
	}

	err = c.service.DeleteDomain(domainRequest.ID)
	if err != nil {
		c.logger.Log(logger.Error, err.Error(), "")
		// TODO: Util to handle err-status mapping
		if err == types.ErrDomainNotFound {
			return nil, fuego.HTTPError{
				Err:    err,
				Status: http.StatusNotFound,
			}
		}

		if err == types.ErrInvalidDomainID || err == types.ErrMissingDomainID {
			return nil, fuego.HTTPError{
				Err:    err,
				Status: http.StatusBadRequest,
			}
		}

		return nil, fuego.HTTPError{
			Err:    err,
			Status: http.StatusInternalServerError,
		}
	}

	return &shared_types.Response{
		Status:  "success",
		Message: "Domain deleted successfully",
	}, nil
}
