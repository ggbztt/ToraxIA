"""
Audit Export Utilities
Exportación de bitácora a CSV y PDF
"""
from datetime import datetime
import pandas as pd
from io import BytesIO
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER


def export_audit_to_csv(logs: list) -> bytes:
    """
    Exporta logs de auditoría a formato CSV.
    
    Args:
        logs: Lista de diccionarios con logs
    
    Returns:
        bytes: Contenido del CSV
    """
    try:
        # Convertir a DataFrame
        df = pd.DataFrame(logs)
        
        # Seleccionar y ordenar columnas
        columns = ['timestamp', 'user_name', 'user_email', 'event_type', 'action', 
                   'entity_type', 'entity_id', 'status', 'details']
        
        # Solo incluir columnas que existan
        available_columns = [col for col in columns if col in df.columns]
        df = df[available_columns]
        
        # Formatear timestamp
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp']).dt.strftime('%d/%m/%Y %H:%M:%S')
        
        # Renombrar columnas a español
        column_names = {
            'timestamp': 'Fecha/Hora',
            'user_name': 'Usuario',
            'user_email': 'Email',
            'event_type': 'Tipo',
            'action': 'Acción',
            'entity_type': 'Entidad',
            'entity_id': 'ID Entidad',
            'status': 'Estado',
            'details': 'Detalles'
        }
        df = df.rename(columns=column_names)
        
        # Convertir a CSV en memoria
        csv_buffer = BytesIO()
        df.to_csv(csv_buffer, index=False, encoding='utf-8-sig')
        csv_buffer.seek(0)
        
        return csv_buffer.getvalue()
        
    except Exception as e:
        print(f"❌ Error al exportar CSV: {e}")
        return None


def export_audit_to_pdf(logs: list) -> bytes:
    """
    Exporta logs de auditoría a formato PDF.
    
    Args:
        logs: Lista de diccionarios con logs
    
    Returns:
        bytes: Contenido del PDF
    """
    try:
        # Crear buffer en memoria
        buffer = BytesIO()
        
        # Crear documento en modo landscape para más espacio
        doc = SimpleDocTemplate(
            buffer,
            pagesize=landscape(letter),
            rightMargin=0.5*inch,
            leftMargin=0.5*inch,
            topMargin=0.75*inch,
            bottomMargin=0.5*inch
        )
        
        story = []
        styles = getSampleStyleSheet()
        
        # Estilo para título
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#1f77b4'),
            spaceAfter=12,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        # Estilo para subtítulo
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#666666'),
            spaceAfter=20,
            alignment=TA_CENTER
        )
        
        # Header
        story.append(Paragraph("ToraxIA - Bitácora del Sistema", title_style))
        story.append(Paragraph(
            f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", 
            subtitle_style
        ))
        
        # Preparar datos para tabla
        table_data = [['Fecha/Hora', 'Usuario', 'Tipo', 'Acción', 'Estado']]
        
        # Estilo para celdas de contenido
        cell_style = ParagraphStyle(
            'CellStyle',
            parent=styles['Normal'],
            fontSize=8,
            leading=10,
            wordWrap='CJK'
        )
        
        for log in logs:
            # Formatear timestamp
            try:
                ts = datetime.fromisoformat(log.get('timestamp', '').replace('Z', '+00:00'))
                formatted_ts = ts.strftime('%d/%m/%Y %H:%M:%S')
            except:
                formatted_ts = log.get('timestamp', 'N/A')
            
            # Traducir event_type
            event_type_map = {
                'auth': 'Autenticación',
                'user_management': 'Gestión Usuarios',
                'analysis': 'Análisis',
                'definition': 'Definiciones',
                'system': 'Sistema'
            }
            event_type = event_type_map.get(log.get('event_type', ''), log.get('event_type', 'N/A'))
            
            # Traducir action
            action_map = {
                'login': 'Inicio sesión',
                'logout': 'Cierre sesión',
                'register': 'Registro',
                'create_user': 'Crear usuario',
                'update_user': 'Actualizar usuario',
                'activate_user': 'Activar usuario',
                'deactivate_user': 'Desactivar usuario',
                'create_analysis': 'Crear análisis',
                'delete_analysis': 'Eliminar análisis',
                'download_pdf': 'Descargar PDF',
                'update_definition': 'Actualizar definición'
            }
            action = action_map.get(log.get('action', ''), log.get('action', 'N/A'))
            
            # Crear Paragraphs para cada celda (permite ajuste automático)
            row = [
                Paragraph(formatted_ts, cell_style),
                Paragraph(log.get('user_name', 'N/A'), cell_style),
                Paragraph(event_type, cell_style),
                Paragraph(action, cell_style),
                Paragraph(log.get('status', 'N/A'), cell_style)
            ]
            
            table_data.append(row)
        
        # Crear tabla con anchos ajustados (sin columna de detalles)
        table = Table(table_data, colWidths=[
            1.8*inch,  # Fecha/Hora
            2.2*inch,  # Usuario
            1.5*inch,  # Tipo
            1.8*inch,  # Acción
            1*inch     # Estado
        ])
        
        # Estilo de tabla
        table.setStyle(TableStyle([
            # Header
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f77b4')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('PADDING', (0, 0), (-1, 0), 6),
            
            # Body
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('ALIGN', (1, 1), (1, -1), 'LEFT'),
            ('ALIGN', (2, 1), (2, -1), 'CENTER'),
            ('ALIGN', (3, 1), (3, -1), 'LEFT'),
            ('ALIGN', (4, 1), (4, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
            ('PADDING', (0, 1), (-1, -1), 4),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),  # Alineación superior para mejor visualización
        ]))
        
        story.append(table)
        
        # Construir PDF
        doc.build(story)
        
        # Obtener bytes
        buffer.seek(0)
        return buffer.getvalue()
        
    except Exception as e:
        print(f"❌ Error al exportar PDF: {e}")
        return None
