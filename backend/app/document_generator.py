from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from docx import Document
import os

def generate_pdf(report_data: dict, output_path: str):
    # Регистрируем DejaVu шрифт
    try:
        pdfmetrics.registerFont(TTFont('DejaVu', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
        pdfmetrics.registerFont(TTFont('DejaVu-Bold', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))
    except:
        pass
    
    doc = SimpleDocTemplate(output_path, pagesize=A4)
    story = []
    styles = getSampleStyleSheet()
    
    # Заголовок
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontName='DejaVu-Bold', fontSize=20)
    story.append(Paragraph('BizEval - Анализ Бизнес-Идеи', title_style))
    story.append(Spacer(1, 20))
    
    cons = report_data['consolidation']
    
    # Summary
    h2_style = ParagraphStyle('CustomH2', parent=styles['Heading2'], fontName='DejaVu-Bold', fontSize=14)
    story.append(Paragraph('Executive Summary', h2_style))
    story.append(Spacer(1, 10))
    
    text_style = ParagraphStyle('CustomText', parent=styles['Normal'], fontName='DejaVu', fontSize=10)
    story.append(Paragraph(cons['executive_summary'], text_style))
    story.append(Spacer(1, 20))
    
    # SWOT
    story.append(Paragraph('SWOT Анализ', h2_style))
    story.append(Spacer(1, 10))
    
    for section, items in [
        ('Сильные стороны', cons['swot']['strengths']),
        ('Слабости', cons['swot']['weaknesses']),
        ('Возможности', cons['swot']['opportunities']),
        ('Угрозы', cons['swot']['threats'])
    ]:
        story.append(Paragraph(f'<b>{section}:</b>', text_style))
        for item in items:
            story.append(Paragraph(f'• {item}', text_style))
        story.append(Spacer(1, 10))
    
    # Рекомендации
    story.append(Paragraph('Рекомендации', h2_style))
    story.append(Spacer(1, 10))
    for i, r in enumerate(cons['recommendations'], 1):
        story.append(Paragraph(f'{i}. {r}', text_style))
    
    story.append(Spacer(1, 20))
    story.append(Paragraph(f'<b>Общая оценка: {cons["overall_score"]}/10</b>', text_style))
    
    doc.build(story)
    return output_path

def generate_docx(report_data: dict, output_path: str):
    doc = Document()
    doc.add_heading('BizEval - Анализ Бизнес-Идеи', 0)
    
    cons = report_data['consolidation']
    
    doc.add_heading('Executive Summary', 1)
    doc.add_paragraph(cons['executive_summary'])
    
    doc.add_heading('SWOT Анализ', 1)
    
    doc.add_heading('Сильные стороны', 2)
    for s in cons['swot']['strengths']:
        doc.add_paragraph(s, style='List Bullet')
    
    doc.add_heading('Слабости', 2)
    for w in cons['swot']['weaknesses']:
        doc.add_paragraph(w, style='List Bullet')
    
    doc.add_heading('Возможности', 2)
    for o in cons['swot']['opportunities']:
        doc.add_paragraph(o, style='List Bullet')
    
    doc.add_heading('Угрозы', 2)
    for t in cons['swot']['threats']:
        doc.add_paragraph(t, style='List Bullet')
    
    doc.add_heading('Рекомендации', 1)
    for i, r in enumerate(cons['recommendations'], 1):
        doc.add_paragraph(f"{i}. {r}")
    
    doc.add_heading(f'Общая оценка: {cons["overall_score"]}/10', 1)
    
    doc.save(output_path)
    return output_path
