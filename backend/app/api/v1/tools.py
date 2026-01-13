"""
工具类API（房贷计算器等）
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Literal

router = APIRouter()


class MortgageCalculateRequest(BaseModel):
    """房贷计算请求"""
    principal: float = Field(..., gt=0, description="贷款本金（元）")
    annual_rate: float = Field(..., gt=0, le=100, description="年利率（%）")
    years: int = Field(..., gt=0, le=50, description="贷款年限（年）")
    payment_type: Literal["equal_principal_interest", "equal_principal"] = Field(
        default="equal_principal_interest",
        description="还款方式：等额本息/等额本金"
    )


class MortgageCalculateResponse(BaseModel):
    """房贷计算结果"""
    monthly_payment: float = Field(..., description="月供（元）")
    total_interest: float = Field(..., description="总利息（元）")
    total_payment: float = Field(..., description="总还款额（元）")
    payment_schedule: list = Field(default=[], description="还款计划（前12个月）")


@router.post("/mortgage-calculator", response_model=MortgageCalculateResponse, summary="房贷计算器")
async def calculate_mortgage(request: MortgageCalculateRequest):
    """
    房贷计算器
    
    支持等额本息和等额本金两种还款方式
    """
    principal = request.principal
    monthly_rate = request.annual_rate / 100 / 12
    months = request.years * 12
    
    if request.payment_type == "equal_principal_interest":
        # 等额本息
        if monthly_rate == 0:
            monthly_payment = principal / months
        else:
            monthly_payment = principal * (
                monthly_rate * (1 + monthly_rate) ** months
            ) / ((1 + monthly_rate) ** months - 1)
        
        total_payment = monthly_payment * months
        total_interest = total_payment - principal
        
        # 生成前12个月的还款计划
        payment_schedule = []
        remaining_principal = principal
        for month in range(1, min(13, months + 1)):
            interest_payment = remaining_principal * monthly_rate
            principal_payment = monthly_payment - interest_payment
            remaining_principal -= principal_payment
            
            payment_schedule.append({
                "month": month,
                "monthly_payment": round(monthly_payment, 2),
                "principal_payment": round(principal_payment, 2),
                "interest_payment": round(interest_payment, 2),
                "remaining_principal": round(remaining_principal, 2)
            })
    
    else:
        # 等额本金
        monthly_principal = principal / months
        total_interest = 0
        payment_schedule = []
        remaining_principal = principal
        
        for month in range(1, min(13, months + 1)):
            interest_payment = remaining_principal * monthly_rate
            monthly_payment = monthly_principal + interest_payment
            remaining_principal -= monthly_principal
            total_interest += interest_payment
            
            payment_schedule.append({
                "month": month,
                "monthly_payment": round(monthly_payment, 2),
                "principal_payment": round(monthly_principal, 2),
                "interest_payment": round(interest_payment, 2),
                "remaining_principal": round(remaining_principal, 2)
            })
        
        total_payment = principal + total_interest
        # 等额本金的月供是递减的，这里返回首月月供
        monthly_payment = payment_schedule[0]["monthly_payment"] if payment_schedule else 0
    
    return {
        "monthly_payment": round(monthly_payment, 2),
        "total_interest": round(total_interest, 2),
        "total_payment": round(total_payment, 2),
        "payment_schedule": payment_schedule
    }
