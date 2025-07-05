from fastapi import FastAPI, Response
from datetime import datetime
from typing import Dict, List, Any

from ..utils.pdf_export import generate_pdf_export

def setup_api_routes(app: FastAPI):
    """Setup API routes for the FastAPI app"""
    
    @app.post("/export-pdf")
    async def export_pdf(data: dict):
        """Export meal plan to PDF"""
        try:
            recipes = data.get('recipes', [])
            shopping_list = data.get('shopping_list', [])
            liked_foods = data.get('liked_foods', [])
            disliked_foods = data.get('disliked_foods', [])
            serving_size = data.get('serving_size', 4)
            
            pdf_data = generate_pdf_export(recipes, shopping_list, liked_foods, disliked_foods, serving_size)
            
            return Response(
                content=pdf_data,
                media_type="application/pdf",
                headers={"Content-Disposition": f"attachment; filename=FoodPal_Meal_Plan_{datetime.now().strftime('%Y%m%d')}.pdf"}
            )
        except Exception as e:
            return {"error": str(e)}