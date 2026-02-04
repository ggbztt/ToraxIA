"""
PDF Report Generator
Genera reportes profesionales en PDF con ReportLab
"""
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from datetime import datetime
from pathlib import Path
import numpy as np
from PIL import Image
import io


def generate_report(analysis_data, output_path=None):
    """
    Genera un reporte PDF profesional con los resultados del análisis.
    
    Args:
        analysis_data (dict): Diccionario con:
            - analysis_id: UUID del análisis
            - timestamp: Fecha/hora del análisis
            - original_image: Array de imagen original
            - overlay: Array de mapa de activación
            - predictions: Array de probabilidades (14)
            - class_names: Lista de nombres de patologías
            - top_class: Nombre de la patología principal
            - top_prob: Probabilidad de la patología principal
        output_path (str): Ruta donde guardar el PDF (opcional, si None genera en memoria)
    
    Returns:
        bytes: Contenido del PDF generado
    """
    
    # Usar BytesIO si no hay output_path
    if output_path is None:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=0.75*inch,
            bottomMargin=0.75*inch
        )
    else:
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=letter,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=0.75*inch,
            bottomMargin=0.75*inch
        )
    
    # Contenedor de elementos
    story = []
    
    # Estilos
    styles = getSampleStyleSheet()
    
    # Estilo personalizado para título
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1f77b4'),
        spaceAfter=12,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    # Estilo para subtítulos
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#666666'),
        spaceAfter=12,
        alignment=TA_CENTER
    )
    
    # Estilo para secciones
    section_style = ParagraphStyle(
        'SectionTitle',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#1f77b4'),
        spaceAfter=10,
        spaceBefore=20,
        fontName='Helvetica-Bold'
    )
    
    # Estilo para disclaimer
    disclaimer_style = ParagraphStyle(
        'Disclaimer',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#d32f2f'),
        alignment=TA_JUSTIFY,
        leftIndent=20,
        rightIndent=20,
        spaceAfter=10
    )
    
    # === HEADER CON LOGO ===
    # Agregar logo de ToraxIA
    from pathlib import Path
    logo_path = Path(__file__).parent.parent / "toraxia_logo" / "toraxia-high-resolution-logo-transparent.png"
    if logo_path.exists():
        logo_img = RLImage(str(logo_path), width=3*inch, height=0.75*inch)
        logo_table = Table([[logo_img]], colWidths=[6*inch])
        logo_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ]))
        story.append(logo_table)
    else:
        story.append(Paragraph("ToraxIA", title_style))
    
    story.append(Paragraph("Reporte de Análisis de Radiografía Torácica", subtitle_style))
    story.append(Spacer(1, 0.2*inch))
    
    # Información del análisis
    analysis_id = analysis_data.get('analysis_id', 'N/A')
    timestamp = analysis_data.get('timestamp', datetime.now().isoformat())
    
    try:
        dt = datetime.fromisoformat(timestamp)
        formatted_date = dt.strftime("%d/%m/%Y %H:%M:%S")
    except:
        formatted_date = timestamp
    
    info_data = [
        ['ID de Análisis:', analysis_id],
        ['Fecha y Hora:', formatted_date],
        ['Modelo:', 'ToraxIA v2.0']
    ]
    
    info_table = Table(info_data, colWidths=[2*inch, 4*inch])
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#1f77b4')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    story.append(info_table)
    story.append(Spacer(1, 0.3*inch))
    
    # === IMÁGENES ===
    story.append(Paragraph("Visualización", section_style))
    
    # Convertir arrays a imágenes PIL y luego a ReportLab
    original_img = analysis_data.get('original_image')
    overlay_img = analysis_data.get('overlay')
    
    images_row = []
    
    if original_img is not None:
        # Convertir array a imagen PIL
        if original_img.max() <= 1.0:
            original_img = (original_img * 255).astype(np.uint8)
        else:
            original_img = original_img.astype(np.uint8)
        
        pil_img = Image.fromarray(original_img)
        
        # Guardar en buffer
        img_buffer = io.BytesIO()
        pil_img.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        
        # Crear imagen ReportLab
        rl_img = RLImage(img_buffer, width=2.5*inch, height=2.5*inch)
        images_row.append(rl_img)
    
    if overlay_img is not None:
        # Convertir array a imagen PIL
        if overlay_img.max() <= 1.0:
            overlay_img = (overlay_img * 255).astype(np.uint8)
        else:
            overlay_img = overlay_img.astype(np.uint8)
        
        pil_overlay = Image.fromarray(overlay_img)
        
        # Guardar en buffer
        overlay_buffer = io.BytesIO()
        pil_overlay.save(overlay_buffer, format='PNG')
        overlay_buffer.seek(0)
        
        # Crear imagen ReportLab
        rl_overlay = RLImage(overlay_buffer, width=2.5*inch, height=2.5*inch)
        images_row.append(rl_overlay)
    
    if images_row:
        images_table = Table([images_row], colWidths=[3*inch, 3*inch])
        images_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(images_table)
        
        # Labels de imágenes
        labels = [['Radiografía Original', 'Mapa de Activación']]
        labels_table = Table(labels, colWidths=[3*inch, 3*inch])
        labels_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#666666')),
        ]))
        story.append(labels_table)
    
    story.append(Spacer(1, 0.3*inch))
    
    # === HALLAZGO PRINCIPAL ===
    story.append(Paragraph("Hallazgo Principal", section_style))
    
    top_class = analysis_data.get('top_class', 'N/A')
    top_prob = analysis_data.get('top_prob', 0.0)
    
    finding_data = [[
        f"{top_class}",
        f"{top_prob*100:.2f}%"
    ]]
    
    finding_table = Table(finding_data, colWidths=[4*inch, 2*inch])
    finding_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 14),
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#1f77b4')),
        ('BOX', (0, 0), (-1, -1), 2, colors.HexColor('#1f77b4')),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f0f2f6')),
        ('PADDING', (0, 0), (-1, -1), 12),
    ]))
    
    story.append(finding_table)
    story.append(Spacer(1, 0.3*inch))
    
    # === TABLA DE PROBABILIDADES ===
    story.append(Paragraph("Probabilidades Completas", section_style))
    
    predictions = analysis_data.get('predictions', [])
    class_names = analysis_data.get('class_names', [])
    
    # Función para determinar nivel de riesgo (texto solamente para PDF)
    def get_risk_level_text(probability):
        """Retorna texto del nivel según el porcentaje"""
        prob_pct = probability * 100
        if prob_pct < 25:
            return "BAJO"
        elif prob_pct < 50:
            return "MODERADO"
        elif prob_pct < 75:
            return "ALTO"
        else:
            return "MUY ALTO"
    
    # Ordenar por probabilidad
    sorted_indices = np.argsort(predictions)[::-1]
    
    # Crear tabla con columna de Nivel
    table_data = [['Patología', 'Probabilidad', 'Nivel']]
    
    for idx in sorted_indices:
        prob = predictions[idx]
        name = class_names[idx]
        level = get_risk_level_text(prob)
        table_data.append([name, f"{prob*100:.2f}%", level])
    
    prob_table = Table(table_data, colWidths=[3.5*inch, 1.5*inch, 1.3*inch])
    prob_table.setStyle(TableStyle([
        # Header
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f77b4')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('PADDING', (0, 0), (-1, 0), 8),
        
        # Body
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),
        ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
        ('ALIGN', (2, 1), (2, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
        ('PADDING', (0, 1), (-1, -1), 6),
    ]))
    
    story.append(prob_table)
    story.append(Spacer(1, 0.4*inch))
    
    # === DISCLAIMER ===
    story.append(Paragraph("IMPORTANTE - Disclaimer Médico", section_style))
    
    disclaimer_text = """
    <b>Esta herramienta es de apoyo educativo y NO sustituye el criterio médico profesional.</b><br/><br/>
    Los resultados presentados en este reporte deben ser interpretados exclusivamente por personal médico calificado. 
    No se deben tomar decisiones clínicas basándose únicamente en este sistema. El modelo de inteligencia artificial 
    utilizado (DenseNet-121) ha sido entrenado con el dataset NIH ChestX-ray14 y tiene un AUC macro de 0.802, 
    pero puede presentar limitaciones y errores. Siempre consulte con un radiólogo o médico especialista para 
    un diagnóstico definitivo.
    """
    
    story.append(Paragraph(disclaimer_text, disclaimer_style))
    
    # === FOOTER ===
    story.append(Spacer(1, 0.2*inch))
    
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#999999'),
        alignment=TA_CENTER
    )
    
    footer_text = f"Generado por ToraxIA - {formatted_date}"
    story.append(Paragraph(footer_text, footer_style))
    
    # Construir PDF
    doc.build(story)
    
    # Retornar bytes según el modo
    if output_path is None:
        # Modo en memoria - retornar desde buffer
        buffer.seek(0)
        return buffer.getvalue()
    else:
        # Modo archivo - leer y retornar
        with open(output_path, 'rb') as f:
            pdf_bytes = f.read()
        return pdf_bytes
