from fastapi import APIRouter

from model_router.service import router_service


router=APIRouter(
    prefix="/api/models",
    tags=["models"]
)


@router.get("/providers")
def providers():

    return {
        "providers":
        router_service.providers()
    }


@router.post("/select")
def select(data:dict):

    return {
        "provider":
        router_service.select(
            data.get("provider")
        )
    }

