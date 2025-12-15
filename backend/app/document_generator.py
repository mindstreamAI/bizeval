from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.colors import HexColor
from docx import Document
from docx.shared import Pt, RGBColor
import os

def generate_pdf(report_data: dict, output_path: str):
    # Регистрируем DejaVu шрифт
    try:
        pdfmetrics.registerFont(TTFont('DejaVu', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
        pdfmetrics.registerFont(TTFont('DejaVu-Bold', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))
    except:
        pass
    
    doc = SimpleDocTemplate(output_path, pagesize=A4, topMargin=40, bottomMargin=40)
    story = []
    styles = getSampleStyleSheet()
    
    # Стили
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], 
                                 fontName='DejaVu-Bold', fontSize=24, textColor=HexColor('#667eea'))
    h1_style = ParagraphStyle('CustomH1', parent=styles['Heading1'], 
                             fontName='DejaVu-Bold', fontSize=16, textColor=HexColor('#333333'))
    h2_style = ParagraphStyle('CustomH2', parent=styles['Heading2'], 
                             fontName='DejaVu-Bold', fontSize=12, textColor=HexColor('#555555'))
    text_style = ParagraphStyle('CustomText', parent=styles['Normal'], 
                                fontName='DejaVu', fontSize=10, leading=14)
    bullet_style = ParagraphStyle('CustomBullet', parent=styles['Normal'],
                                  fontName='DejaVu', fontSize=10, leftIndent=20, leading=14)
    
    cons = report_data['consolidation']
    
    # Заголовок
    story.append(Paragraph('🚀 BizEval', title_style))
    story.append(Paragraph('Комплексный Анализ Бизнес-Идеи', h2_style))
    story.append(Spacer(1, 30))
    
    # Executive Summary
    story.append(Paragraph('📊 Executive Summary', h1_style))
    story.append(Spacer(1, 10))
    story.append(Paragraph(cons['executive_summary'], text_style))
    story.append(Spacer(1, 20))
    
    # Audience Analysis
    aud = cons.get('audience_analysis', {})
    story.append(Paragraph('👥 Анализ Целевой Аудитории', h1_style))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph(f'<b>Приоритетный сегмент:</b> {aud.get("priority_segment", "N/A")}', text_style))
    story.append(Paragraph(f'<b>Product-Market Fit:</b> {aud.get("market_fit_score", 0)}/10', text_style))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph('<b>Ключевые сегменты:</b>', text_style))
    for seg in aud.get('key_segments', []):
        story.append(Paragraph(f'• {seg}', bullet_style))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph('<b>Ключевые инсайты:</b>', text_style))
    for insight in aud.get('key_insights', []):
        story.append(Paragraph(f'• {insight}', bullet_style))
    story.append(Spacer(1, 20))
    
    # Competitive Landscape
    comp = cons.get('competitive_landscape', {})
    story.append(Paragraph('🌍 Конкурентная Среда', h1_style))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph(f'<b>Уровень конкуренции:</b> {comp.get("competition_intensity", 0)}/10', text_style))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph('<b>Главные конкуренты:</b>', text_style))
    for competitor in comp.get('main_competitors', []):
        story.append(Paragraph(f'• {competitor}', bullet_style))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph('<b>Незанятые ниши:</b>', text_style))
    for gap in comp.get('market_gaps', []):
        story.append(Paragraph(f'• {gap}', bullet_style))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph('<b>Best Practices:</b>', text_style))
    for practice in comp.get('best_practices', []):
        story.append(Paragraph(f'• {practice}', bullet_style))
    story.append(Spacer(1, 20))
    
    # Local Market
    local = cons.get('local_market', {})
    story.append(Paragraph('📍 Локальный Рынок', h1_style))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph(f'<b>Привлекательность рынка:</b> {local.get("market_attractiveness", 0)}/10', text_style))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph('<b>Ключевые тренды:</b>', text_style))
    for trend in local.get('key_trends', []):
        story.append(Paragraph(f'• {trend}', bullet_style))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph('<b>Локальные конкуренты:</b>', text_style))
    for lcomp in local.get('local_competitors', []):
        story.append(Paragraph(f'• {lcomp}', bullet_style))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph('<b>Региональная специфика:</b>', text_style))
    for spec in local.get('regional_specifics', []):
        story.append(Paragraph(f'• {spec}', bullet_style))
    story.append(Spacer(1, 20))
    
    # SWOT
    story.append(Paragraph('🎯 SWOT Анализ', h1_style))
    story.append(Spacer(1, 10))
    
    for section, items in [
        ('✅ Сильные стороны (Strengths)', cons['swot']['strengths']),
        ('⚠️ Слабости (Weaknesses)', cons['swot']['weaknesses']),
        ('🚀 Возможности (Opportunities)', cons['swot']['opportunities']),
        ('⚡ Угрозы (Threats)', cons['swot']['threats'])
    ]:
        story.append(Paragraph(f'<b>{section}:</b>', text_style))
        for item in items:
            story.append(Paragraph(f'• {item}', bullet_style))
        story.append(Spacer(1, 10))
    
    story.append(Spacer(1, 10))
    
    # Strategic Recommendations
    story.append(Paragraph('💡 Стратегические Рекомендации', h1_style))
    story.append(Spacer(1, 10))
    
    # Группируем по priority
    high_recs = [r for r in cons.get('strategic_recommendations', []) if r.get('priority') == 'high']
    medium_recs = [r for r in cons.get('strategic_recommendations', []) if r.get('priority') == 'medium']
    low_recs = [r for r in cons.get('strategic_recommendations', []) if r.get('priority') == 'low']
    
    for priority, recs, emoji in [('Высокий приоритет', high_recs, '🔴'), 
                                   ('Средний приоритет', medium_recs, '🟡'), 
                                   ('Низкий приоритет', low_recs, '🟢')]:
        if recs:
            story.append(Paragraph(f'<b>{emoji} {priority}:</b>', text_style))
            story.append(Spacer(1, 5))
            for i, rec in enumerate(recs, 1):
                cat_emoji = {'product': '🛠️', 'marketing': '📢', 'business_model': '💰', 'risks': '⚠️'}.get(rec.get('category'), '•')
                story.append(Paragraph(f'<b>{cat_emoji} {rec.get("recommendation", "")}</b>', text_style))
                story.append(Paragraph(f'<i>{rec.get("rationale", "")}</i>', bullet_style))
                story.append(Spacer(1, 8))
    
    story.append(Spacer(1, 20))
    
    # Итоговая оценка
    score = cons.get('overall_score', 0)
    risk = cons.get('risk_level', 'medium')
    readiness = cons.get('investment_readiness', 'idea_stage')
    
    risk_emoji = {'low': '🟢', 'medium': '🟡', 'high': '🔴'}.get(risk, '🟡')
    
    story.append(Paragraph('⭐ Итоговая Оценка', h1_style))
    story.append(Spacer(1, 10))
    story.append(Paragraph(f'<b>Общий балл:</b> {score}/10', text_style))
    story.append(Paragraph(f'<b>Уровень риска:</b> {risk_emoji} {risk.upper()}', text_style))
    story.append(Paragraph(f'<b>Готовность к инвестициям:</b> {readiness.replace("_", " ").title()}', text_style))
    
    doc.build(story)
    return output_path


def generate_docx(report_data: dict, output_path: str):
    doc = Document()
    cons = report_data['consolidation']
    
    # Заголовок
    title = doc.add_heading('🚀 BizEval', 0)
    title.runs[0].font.color.rgb = RGBColor(102, 126, 234)
    doc.add_heading('Комплексный Анализ Бизнес-Идеи', level=2)
    
    # Executive Summary
    doc.add_heading('📊 Executive Summary', level=1)
    doc.add_paragraph(cons['executive_summary'])
    
    # Audience Analysis
    aud = cons.get('audience_analysis', {})
    doc.add_heading('👥 Анализ Целевой Аудитории', level=1)
    doc.add_paragraph(f"Приоритетный сегмент: {aud.get('priority_segment', 'N/A')}")
    doc.add_paragraph(f"Product-Market Fit: {aud.get('market_fit_score', 0)}/10")
    
    doc.add_heading('Ключевые сегменты:', level=2)
    for seg in aud.get('key_segments', []):
        doc.add_paragraph(seg, style='List Bullet')
    
    doc.add_heading('Ключевые инсайты:', level=2)
    for insight in aud.get('key_insights', []):
        doc.add_paragraph(insight, style='List Bullet')
    
    # Competitive Landscape
    comp = cons.get('competitive_landscape', {})
    doc.add_heading('🌍 Конкурентная Среда', level=1)
    doc.add_paragraph(f"Уровень конкуренции: {comp.get('competition_intensity', 0)}/10")
    
    doc.add_heading('Главные конкуренты:', level=2)
    for competitor in comp.get('main_competitors', []):
        doc.add_paragraph(competitor, style='List Bullet')
    
    doc.add_heading('Незанятые ниши:', level=2)
    for gap in comp.get('market_gaps', []):
        doc.add_paragraph(gap, style='List Bullet')
    
    doc.add_heading('Best Practices:', level=2)
    for practice in comp.get('best_practices', []):
        doc.add_paragraph(practice, style='List Bullet')
    
    # Local Market
    local = cons.get('local_market', {})
    doc.add_heading('📍 Локальный Рынок', level=1)
    doc.add_paragraph(f"Привлекательность рынка: {local.get('market_attractiveness', 0)}/10")
    
    doc.add_heading('Ключевые тренды:', level=2)
    for trend in local.get('key_trends', []):
        doc.add_paragraph(trend, style='List Bullet')
    
    doc.add_heading('Локальные конкуренты:', level=2)
    for lcomp in local.get('local_competitors', []):
        doc.add_paragraph(lcomp, style='List Bullet')
    
    doc.add_heading('Региональная специфика:', level=2)
    for spec in local.get('regional_specifics', []):
        doc.add_paragraph(spec, style='List Bullet')
    
    # SWOT
    doc.add_heading('🎯 SWOT Анализ', level=1)
    
    doc.add_heading('✅ Сильные стороны (Strengths)', level=2)
    for s in cons['swot']['strengths']:
        doc.add_paragraph(s, style='List Bullet')
    
    doc.add_heading('⚠️ Слабости (Weaknesses)', level=2)
    for w in cons['swot']['weaknesses']:
        doc.add_paragraph(w, style='List Bullet')
    
    doc.add_heading('🚀 Возможности (Opportunities)', level=2)
    for o in cons['swot']['opportunities']:
        doc.add_paragraph(o, style='List Bullet')
    
    doc.add_heading('⚡ Угрозы (Threats)', level=2)
    for t in cons['swot']['threats']:
        doc.add_paragraph(t, style='List Bullet')
    
    # Strategic Recommendations
    doc.add_heading('💡 Стратегические Рекомендации', level=1)
    
    high_recs = [r for r in cons.get('strategic_recommendations', []) if r.get('priority') == 'high']
    medium_recs = [r for r in cons.get('strategic_recommendations', []) if r.get('priority') == 'medium']
    low_recs = [r for r in cons.get('strategic_recommendations', []) if r.get('priority') == 'low']
    
    for priority, recs, emoji in [('Высокий приоритет', high_recs, '🔴'),
                                   ('Средний приоритет', medium_recs, '🟡'),
                                   ('Низкий приоритет', low_recs, '🟢')]:
        if recs:
            doc.add_heading(f'{emoji} {priority}', level=2)
            for rec in recs:
                cat_emoji = {'product': '🛠️', 'marketing': '📢', 'business_model': '💰', 'risks': '⚠️'}.get(rec.get('category'), '•')
                p = doc.add_paragraph()
                p.add_run(f"{cat_emoji} {rec.get('recommendation', '')}").bold = True
                doc.add_paragraph(f"  → {rec.get('rationale', '')}", style='List Bullet')
    
    # Итоговая оценка
    score = cons.get('overall_score', 0)
    risk = cons.get('risk_level', 'medium')
    readiness = cons.get('investment_readiness', 'idea_stage')
    
    risk_emoji = {'low': '🟢', 'medium': '🟡', 'high': '🔴'}.get(risk, '🟡')
    
    doc.add_heading('⭐ Итоговая Оценка', level=1)
    doc.add_paragraph(f"Общий балл: {score}/10")
    doc.add_paragraph(f"Уровень риска: {risk_emoji} {risk.upper()}")
    doc.add_paragraph(f"Готовность к инвестициям: {readiness.replace('_', ' ').title()}")
    
    doc.save(output_path)
    return output_path
