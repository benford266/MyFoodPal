"""
Meal Plan API Routes
"""
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from datetime import datetime
import json

from ...database.connection import get_db
from ...database.models import User, MealPlan
from ...models.schemas import PDFExportRequest
from ...services.auth import AuthService
from ...utils.pdf_export import generate_pdf_export

router = APIRouter()
auth_service = AuthService()


@router.post("/{meal_plan_id}/export-pdf")
async def export_meal_plan_pdf(
    meal_plan_id: int,
    current_user: User = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db)
):
    """Export meal plan to PDF"""
    
    # Get meal plan
    meal_plan = db.query(MealPlan).filter(
        MealPlan.id == meal_plan_id,
        MealPlan.user_id == current_user.id
    ).first()
    
    if not meal_plan:
        raise HTTPException(status_code=404, detail="Meal plan not found")
    
    try:
        recipes = json.loads(meal_plan.recipes_json)
        shopping_list = json.loads(meal_plan.shopping_list_json)
        liked_foods = meal_plan.liked_foods_snapshot.split(",") if meal_plan.liked_foods_snapshot else []
        disliked_foods = meal_plan.disliked_foods_snapshot.split(",") if meal_plan.disliked_foods_snapshot else []
        
        pdf_data = generate_pdf_export(
            recipes, 
            shopping_list, 
            liked_foods, 
            disliked_foods, 
            meal_plan.serving_size
        )
        
        return Response(
            content=pdf_data,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=FoodPal_Meal_Plan_{meal_plan.id}_{datetime.now().strftime('%Y%m%d')}.pdf"
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF export failed: {str(e)}")


@router.post("/export-pdf")
async def export_custom_pdf(data: PDFExportRequest):
    """Export custom meal plan data to PDF"""
    try:
        pdf_data = generate_pdf_export(
            data.recipes, 
            data.shopping_list, 
            data.liked_foods, 
            data.disliked_foods, 
            data.serving_size
        )
        
        return Response(
            content=pdf_data,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=FoodPal_Meal_Plan_{datetime.now().strftime('%Y%m%d')}.pdf"
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF export failed: {str(e)}")