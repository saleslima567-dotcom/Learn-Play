from datetime import timezone
from io import BytesIO
from xml.sax.saxutils import escape
from zoneinfo import ZoneInfo

import qrcode
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer


METHODS = {'pix': 'Pix', 'credit': 'Cartão de crédito', 'debit': 'Cartão de débito'}


def payment_qr(reference):
    buffer = BytesIO()
    image = qrcode.make(f'LEARNPLAY-DEMO:{reference}', box_size=6)
    image.save(buffer, format='PNG')
    buffer.seek(0)
    return buffer


def payment_receipt(payment, buyer):
    buffer = BytesIO()
    styles = getSampleStyleSheet()
    styles['Title'].textColor = colors.HexColor('#87283f')
    brl = f'{payment.amount:,.2f}'.translate(str.maketrans(',.', '.,'))
    date = payment.approved_at.replace(tzinfo=timezone.utc).astimezone(ZoneInfo('America/Fortaleza')).strftime('%d/%m/%Y às %H:%M')
    fields = [
        ('Curso', payment.course_title),
        ('Aluno', buyer),
        ('Valor simulado', f'R$ {brl}'),
        ('Forma de pagamento', METHODS[payment.method]),
        ('Data da simulação (horário de Brasília)', date),
        ('Referência da simulação', payment.reference),
    ]
    elements = [Paragraph('LearnPlay', styles['Heading2']), Paragraph('Comprovante de pagamento simulado', styles['Title'])]
    elements.append(Paragraph('Demonstração acadêmica. Nenhuma cobrança foi realizada.', styles['Normal']))
    for label, value in fields:
        elements.extend([Spacer(1, 10), Paragraph(f'<b>{label}</b><br/>{escape(value)}', styles['Normal'])])
    SimpleDocTemplate(buffer, pagesize=A4, title='Comprovante de pagamento LearnPlay').build(elements)
    buffer.seek(0)
    return buffer
