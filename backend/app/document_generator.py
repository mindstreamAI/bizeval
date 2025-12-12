from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from docx import Document
from docx.shared import Pt, RGBColor
import os
import json

def generate_pdf(report_data: dict, output_path: str):
    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4
    y = height - inch
    
    c.setFont("Helvetica-Bold", 16)
    c.drawString(inch, y, "BizEval - Анализ Бизнес-Идеи")
    y -= 0.5*inch
    
    c.setFont("Helvetica", 10)
    cons = report_data['consolidation']
    
    # Summary
    c.drawString(inch, y, "Executive Summary:")
    y -= 0.3*inch
    for line in cons['executive_summary'][:200].split('\n'):
        c.drawString(inch, y, line[:80])
        y -= 0.2*inch
    
    # SWOT
    y -= 0.3*inch
    c.setFont("Helvetica-Bold", 12)
    c.drawString(inch, y, "SWOT:")
    y -= 0.3*inch
    
    c.setFont("Helvetica", 10)
    for s in cons['swot']['strengths'][:2]:
        c.drawString(inch, y, f"+ {s[:70]}")
        y -= 0.2*inch
    
    c.save()
    return output_path

def generate_docx(report_data: dict, output_path: str):
    doc = Document()
    doc.add_heading('BizEval - Анализ Бизнес-Идеи', 0)
    
    cons = report_data['consolidation']
    
    doc.add_heading('Executive Summary', 1)
    doc.add_paragraph(cons['executive_summary'])
    
    doc.add_heading('SWOT Анализ', 1)
    
    doc.add_heading('Strengths', 2)
    for s in cons['swot']['strengths']:
        doc.add_paragraph(s, style='List Bullet')
    
    doc.add_heading('Weaknesses', 2)
    for w in cons['swot']['weaknesses']:
        doc.add_paragraph(w, style='List Bullet')
    
    doc.add_heading('Opportunities', 2)
    for o in cons['swot']['opportunities']:
        doc.add_paragraph(o, style='List Bullet')
    
    doc.add_heading('Threats', 2)
    for t in cons['swot']['threats']:
        doc.add_paragraph(t, style='List Bullet')
    
    doc.add_heading('Рекомендации', 1)
    for i, r in enumerate(cons['recommendations'], 1):
        doc.add_paragraph(f"{i}. {r}")
    
    doc.save(output_path)
    return output_path
