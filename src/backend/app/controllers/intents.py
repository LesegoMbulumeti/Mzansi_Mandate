from fastapi import APIRouter

from app.schemas.intent import IntentIn, IntentOut

router = APIRouter(prefix="/api/v1/intents", tags=["intents"])


@router.post("", response_model=IntentOut)
async def submit_intent(body: IntentIn) -> IntentOut:
    # TODO: call PaymentOrchestrator (policy check -> sign -> audit). Controllers stay thin.
    return IntentOut(verdict="blocked", detail="not implemented")
