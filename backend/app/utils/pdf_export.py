"""
PDF Export Utilities
"""
import io
from datetime import datetime
from typing import List, Dict, Any
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT


def generate_pdf_export(recipes: List[Dict[str, Any]], 
                       shopping_list: List[Dict[str, str]], 
                       liked_foods: List[str], 
                       disliked_foods: List[str], 
                       serving_size: int) -> bytes:
    """
    Generate a PDF with recipes and shopping list
    
    Args:
        recipes: List of recipe dictionaries
        shopping_list: List of shopping list items
        liked_foods: User's liked foods
        disliked_foods: User's disliked foods
        serving_size: Number of servings
        
    Returns:
        PDF data as bytes
    """
    
    # Create PDF buffer
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, 
                          topMargin=72, bottomMargin=72)
    
    # Get styles
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#059669')
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=16,
        spaceAfter=20,
        textColor=colors.HexColor('#374151')
    )
    
    recipe_title_style = ParagraphStyle(
        'RecipeTitle',
        parent=styles['Heading3'],
        fontSize=14,
        spaceBefore=20,
        spaceAfter=10,
        textColor=colors.HexColor('#059669')
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=6,
        leftIndent=20
    )
    
    # Build PDF content
    story = []
    
    # Title page
    story.append(Paragraph("🍽️ FoodPal Meal Plan", title_style))
    story.append(Spacer(1, 20))
    
    # Meal plan info
    current_date = datetime.now().strftime("%B %d, %Y")
    story.append(Paragraph(f"Generated on: {current_date}", styles['Normal']))
    story.append(Paragraph(f"Serving size: {serving_size} people", styles['Normal']))
    story.append(Paragraph(f"Number of recipes: {len([r for r in recipes if 'error' not in r])}", styles['Normal']))
    story.append(Spacer(1, 30))
    
    # Food preferences
    if liked_foods or disliked_foods:
        story.append(Paragraph("Food Preferences", subtitle_style))
        if liked_foods:
            liked_text = ', '.join([f for f in liked_foods if f.strip()])
            if liked_text:
                story.append(Paragraph(f"<b>Likes:</b> {liked_text}", styles['Normal']))
        if disliked_foods:
            disliked_text = ', '.join([f for f in disliked_foods if f.strip()])
            if disliked_text:
                story.append(Paragraph(f"<b>Avoids:</b> {disliked_text}", styles['Normal']))
        story.append(Spacer(1, 30))
    
    # Shopping List
    if shopping_list:
        story.append(Paragraph("🛒 Shopping List", subtitle_style))
        
        # Create table for shopping list
        shopping_data = [['Quantity', 'Unit', 'Item']]
        for item in shopping_list:
            # Handle both old and new shopping list formats
            ingredient_name = item.get('ingredient', item.get('item', ''))
            shopping_data.append([
                item.get('quantity', ''),
                item.get('unit', ''),
                ingredient_name
            ])
        
        shopping_table = Table(shopping_data, colWidths=[1*inch, 1*inch, 4*inch])
        shopping_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#059669')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')])
        ]))
        
        story.append(shopping_table)
        story.append(PageBreak())
    
    # Recipes
    story.append(Paragraph("📖 Recipes", subtitle_style))
    
    recipe_count = 0
    for i, recipe in enumerate(recipes, 1):
        if "error" in recipe:
            continue
            
        recipe_count += 1
        
        # Recipe title
        recipe_name = recipe.get('name', f'Recipe {recipe_count}')
        story.append(Paragraph(f"{recipe_count}. {recipe_name}", recipe_title_style))
        
        # Recipe info
        prep_time = recipe.get('prep_time', 'N/A')
        cook_time = recipe.get('cook_time', 'N/A')
        servings = recipe.get('servings', serving_size)
        difficulty = recipe.get('difficulty', 'Medium')
        cuisine = recipe.get('cuisine_inspiration', '')
        
        info_parts = [f"<b>Prep:</b> {prep_time}", f"<b>Cook:</b> {cook_time}", f"<b>Serves:</b> {servings}"]
        if difficulty:
            info_parts.append(f"<b>Difficulty:</b> {difficulty}")
        if cuisine:
            info_parts.append(f"<b>Cuisine:</b> {cuisine}")
            
        info_text = " | ".join(info_parts)
        story.append(Paragraph(info_text, styles['Normal']))
        story.append(Spacer(1, 10))
        
        # Ingredients
        story.append(Paragraph("<b>Ingredients:</b>", styles['Normal']))
        if "ingredients" in recipe:
            for ingredient in recipe["ingredients"]:
                if isinstance(ingredient, dict):
                    quantity = ingredient.get("quantity", "")
                    unit = ingredient.get("unit", "")
                    item = ingredient.get("item", "")
                    ingredient_text = f"• {quantity} {unit} {item}".strip()
                else:
                    ingredient_text = f"• {ingredient}"
                story.append(Paragraph(ingredient_text, normal_style))
        story.append(Spacer(1, 10))
        
        # Instructions
        story.append(Paragraph("<b>Instructions:</b>", styles['Normal']))
        if "instructions" in recipe:
            for j, instruction in enumerate(recipe["instructions"], 1):
                story.append(Paragraph(f"{j}. {instruction}", normal_style))
        
        # Add space between recipes (except for last one)
        if recipe_count < len([r for r in recipes if 'error' not in r]):
            story.append(Spacer(1, 30))
    
    # Build PDF
    doc.build(story)
    
    # Get PDF data
    pdf_data = buffer.getvalue()
    buffer.close()
    
    return pdf_data