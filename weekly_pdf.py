#!/usr/bin/env python3
"""Server-side weekly intelligence PDF in the Portafolio Manager dark visual system."""
import sys, json, io, math, html, os
from datetime import datetime, timezone
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Flowable, KeepTogether, HRFlowable
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor

BGC=HexColor('#0b1210');PANEL=HexColor('#14201b');PANEL2=HexColor('#192820');BORDER=HexColor('#2a3e34');INK=HexColor('#e8f0ea');MUTED=HexColor('#9cb0a3');MINT=HexColor('#53c5a5');AMBER=HexColor('#d9b46f');RED=HexColor('#ef988d')
for name,path in [('Lato','/usr/share/fonts/truetype/lato/Lato-Regular.ttf'),('Lato-Bold','/usr/share/fonts/truetype/lato/Lato-Bold.ttf')]:
    if os.path.exists(path): pdfmetrics.registerFont(TTFont(name,path))
FONT='Lato' if 'Lato' in pdfmetrics.getRegisteredFontNames() else 'Helvetica'
BOLD='Lato-Bold' if 'Lato-Bold' in pdfmetrics.getRegisteredFontNames() else 'Helvetica-Bold'
SW,SH=A4; PAD=37; W=SW-PAD*2
style={
 'h1':ParagraphStyle('H1',fontName=BOLD,fontSize=25,leading=31,textColor=INK,spaceAfter=12),
 'h2':ParagraphStyle('H2',fontName=BOLD,fontSize=17,leading=22,textColor=INK,spaceBefore=10,spaceAfter=8,keepWithNext=True),
 'h3':ParagraphStyle('H3',fontName=BOLD,fontSize=11,leading=16,textColor=MINT,spaceBefore=11,spaceAfter=5,keepWithNext=True),
 'body':ParagraphStyle('Body',fontName=FONT,fontSize=9.3,leading=14.5,textColor=INK,spaceAfter=8),
 'small':ParagraphStyle('Small',fontName=FONT,fontSize=8.0,leading=12,textColor=MUTED,spaceAfter=5),
 'caption':ParagraphStyle('Caption',fontName=BOLD,fontSize=7.4,leading=10.5,textColor=MINT,spaceAfter=7),
 'cell':ParagraphStyle('Cell',fontName=FONT,fontSize=8,leading=11.4,textColor=INK),
 'cellr':ParagraphStyle('Cellr',fontName=FONT,fontSize=8,leading=11.4,textColor=INK,alignment=TA_RIGHT),
 'head':ParagraphStyle('Head',fontName=BOLD,fontSize=7.7,leading=10.5,textColor=MUTED),
 'headr':ParagraphStyle('Headr',fontName=BOLD,fontSize=7.7,leading=10.5,textColor=MUTED,alignment=TA_RIGHT),
}
def E(x):return html.escape(str(x if x is not None else '—'))
def P(t,k='body'):return Paragraph(t,style[k])
def usd(v):return '${:,.2f}'.format(v) if isinstance(v,(float,int)) and math.isfinite(v) else 'N/A'
def pct(v):return ('{:+.2f}%'.format(v)) if isinstance(v,(float,int)) and math.isfinite(v) else 'N/A'
def num(v):return '{:,.1f}'.format(v) if isinstance(v,(float,int)) and math.isfinite(v) else 'N/A'
def date(v):return str(v or '')[:10] or 'Unverified'
def divider():return HRFlowable(width='100%',thickness=.7,color=BORDER,spaceBefore=11,spaceAfter=14)
def cell(x,head=False,right=False):return P(E(x),'headr' if head and right else 'head' if head else 'cellr' if right else 'cell')
def table(headers,rows,widths=None):
    if not rows:return [P('No verified data available for this section.','small')]
    data=[[cell(h,True,i>0) for i,h in enumerate(headers)]]
    for row in rows:data.append([cell(item,False,i>0) for i,item in enumerate(row)])
    t=Table(data,colWidths=widths or [W/len(headers)]*len(headers),repeatRows=1,hAlign='LEFT')
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),PANEL2),('ROWBACKGROUNDS',(0,1),(-1,-1),[PANEL,BGC]),('LINEBELOW',(0,0),(-1,0),.8,BORDER),('LINEBELOW',(0,1),(-1,-1),.3,BORDER),('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),6.5),('BOTTOMPADDING',(0,0),(-1,-1),6.5),('VALIGN',(0,0),(-1,-1),'MIDDLE')]))
    return [t]
class ExposureBars(Flowable):
    def __init__(self,records,height=115):Flowable.__init__(self);self.records=records[:6];self.width=W;self.height=max(42,min(height,len(self.records)*15+9))
    def draw(self):
        c=self.canv;top=self.height-10
        for i,item in enumerate(self.records):
            y=top-i*15;c.setFont(FONT,8);c.setFillColor(INK);c.drawString(0,y,html.unescape(E(item.get('name',''))[:43]));c.setFont(BOLD,8);c.setFillColor(MINT);c.drawRightString(W,y,f"{item.get('weight',0):.1f}%")
            c.setFillColor(PANEL2);c.roundRect(0,y-8,W,4,2,stroke=0,fill=1);c.setFillColor(MINT);c.roundRect(0,y-8,max(1,W*min(100,item.get('weight',0))/100),4,2,stroke=0,fill=1)
class MetricStrip(Flowable):
    def __init__(self,blocks):Flowable.__init__(self);self.blocks=blocks;self.width=W;self.height=76
    def draw(self):
        c=self.canv;n=len(self.blocks);gap=8;w=(W-(n-1)*gap)/n
        for i,(label,value) in enumerate(self.blocks):
            x=i*(w+gap);c.setFillColor(PANEL);c.setStrokeColor(BORDER);c.roundRect(x,0,w,72,7,stroke=1,fill=1);c.setFillColor(MUTED);c.setFont(FONT,7.8);c.drawString(x+10,50,label[:25]);c.setFillColor(INK);c.setFont(BOLD,13.2 if len(str(value))<14 else 10);c.drawString(x+10,23,str(value)[:27])
def section(story,num,title,deck=''):
    story.extend([P(f'SECTION {num:02d} / WEEKLY INTELLIGENCE','caption'),P(E(title),'h1')]);
    if deck: story.append(P(E(deck),'small'))
def lines_of_items(items,limit=6):
    out=[]
    for obj in items[:limit]:
        title=E(obj.get('title',''));source=E(obj.get('source',''));published=date(obj.get('publishedAt'));url=obj.get('url','')
        line=f'<b>{title}</b><br/><font color="#9cb0a3">{source} | {published} | {E(obj.get("theme",""))}</font>'
        if str(url).startswith('https://'):line+=f' | <link color="#53c5a5" href="{html.escape(url,quote=True)}">Original article</link>'
        out.append(P(line,'body'))
    return out
class DarkDoc(SimpleDocTemplate): pass

def build(report):
    output=io.BytesIO();sample=report.get('id')=='illustrative-only';sampledata=bool(report.get('sampleData'));doc=DarkDoc(output,pagesize=A4,leftMargin=PAD,rightMargin=PAD,topMargin=75,bottomMargin=57,title='Portafolio Manager | Weekly Portfolio Intelligence',author='Portafolio Manager',pageCompression=1)
    def frame(c,doc):
        c.saveState();c.setFillColor(BGC);c.rect(0,0,SW,SH,stroke=0,fill=1);c.setStrokeColor(BORDER);c.setLineWidth(.6);c.line(PAD,SH-50,SW-PAD,SH-50);c.line(PAD,40,SW-PAD,40)
        c.setFont(BOLD,9);c.setFillColor(MINT);c.drawString(PAD,SH-34,'PORTAFOLIO MANAGER');c.setFont(FONT,8);c.setFillColor(MUTED);c.drawRightString(SW-PAD,SH-34,'WEEKLY PORTFOLIO INTELLIGENCE');c.drawString(PAD,27,'SAMPLE DATA  |  NOT YOUR HOLDINGS' if sampledata else 'ILLUSTRATIVE SAMPLE  |  NOT A REAL ACCOUNT' if sample else 'INTERNAL RESEARCH  |  DATA IS SUBJECT TO SOURCE LIMITATIONS');c.drawRightString(SW-PAD,27,f'{doc.page:02d}');c.restoreState()
    st=[];s=report.get('summary',{});lines=report.get('lines',[]);risks=report.get('risk',[]);news=report.get('intelligence',{}).get('items',[])
    if sampledata: st.append(P('<b>SAMPLE DATA — not your holdings.</b> This account still contains the demonstration portfolio; import your Yahoo Finance holdings for a real review.','h3'))
    section(st,1,'Portfolio review',f"{'SAMPLE DATA — NOT YOUR HOLDINGS | ' if sampledata else 'ILLUSTRATIVE SAMPLE | ' if sample else ''}Generated {date(report.get('generatedAt'))} | Time zone {report.get('timezone','')} | Market snapshot {date(report.get('asOfMarket'))}")
    complete=bool(report.get('valuationComplete'));notdetailed=int(report.get('holdingsNotDetailed') or 0)
    covtxt=f"{E(s.get('coverage'))}"+(f" ({num(s.get('coveragePct'))}%)" if s.get('coveragePct') is not None else '')
    st.extend([MetricStrip([('POSITION VALUE',usd(s.get('totalValue'))) if complete else ('PRICED VALUE (PARTIAL)',usd(s.get('verifiedValue'))),('UNREALIZED P/L',usd(s.get('unrealized'))),('QUOTE COVERAGE',f"{s.get('coverage','N/A')}"),('WEEKLY MOVE*',pct(s.get('weekProxy')))]),Spacer(1,16),P('Executive assessment','h2')]);
    if not lines:st.append(P('No holdings have been imported for this account. Import a Yahoo Finance portfolio export to populate analysis. Quotes alone do not identify your private holdings.'))
    else:
        missing=s.get('unpriced') or []
        reasons=s.get('unpricedReasons') or {}
        unpriced_txt=(f" Unpriced: {E(', '.join((m+' ('+reasons[m]+')') if reasons.get(m) else m for m in missing[:12]))}"+(f" and {len(missing)-12} more" if len(missing)>12 else '')+'.') if missing else ''
        st.append(P(f"Quote coverage: <b>{covtxt}</b> positions. Portfolio-level valuation is {'complete' if complete else 'incomplete; excluded prices are not guessed, and total value and P/L are withheld'}.{unpriced_txt} Unrealized gain/loss compares current prices with imported cost basis, not with time-weighted historical performance."))
        if notdetailed: st.append(P(f"<b>{notdetailed} holdings not detailed</b> in the holdings table; they are included in value, P/L and coverage figures.",'small'))
        st.append(P(f"Approximate current-weight daily move: <b>{pct(s.get('dayProxy'))}</b>. Monthly current-weight proxy: <b>{pct(s.get('monthProxy'))}</b>. Return coverage (day/week/month): {E(s.get('dayProxyCoverage'))}, {E(s.get('weekProxyCoverage'))}, {E(s.get('monthProxyCoverage'))} positions; holdings without a return are excluded, not counted as 0%. These are <b>not</b> broker-confirmed account returns."))
    st.append(P('Risk register','h2'))
    if risks: st.extend(table(['SEVERITY','EXPOSURE','REASON'],[[x.get('level'),x.get('title'),x.get('detail')] for x in risks[:7]],[74,194,W-268]))
    else:st.append(P('No concentration exceptions detected in available priced positions; this is not evidence of a fully diversified portfolio.','small'))
    st.extend([Spacer(1,11),P('Focus for the coming week','h2'),P('Review reported earnings and guidance for core holdings; watch company-specific SEC filings and material changes in rates, energy availability, export restrictions and geopolitical risk. Signals should be evaluated against verified fundamentals and portfolio position limits.'),P('* Current-weight return proxy, not an actual time-weighted or money-weighted account return.','small')])
    st.append(PageBreak());section(st,2,'Holdings & portfolio structure','Prices sourced from the Yahoo Finance public market feed where available; quantities originate from your imported ledger.')
    limit=int(report.get('detailLimit') or len(lines) or 1)
    st.extend(table(['TICKER','SHARES','PRICE','VALUE','WEIGHT','P/L'],[[x['ticker'],num(x.get('shares')),usd(x.get('price')),usd(x.get('value')),num(x.get('weight'))+'%' if x.get('weight') is not None else 'N/A',usd(x.get('gain'))] for x in sorted(lines,key=lambda v:v.get('value') or -1,reverse=True)[:limit]],[66,69,85,102,73,W-395]))
    if notdetailed: st.append(P(f'{notdetailed} holdings not detailed in this table (largest {limit} by value shown). Value, P/L and coverage include every holding.','small'))
    if lines and not complete: st.append(P(f'Quote coverage {covtxt}: weights are shares of the priced subset only.','small'))
    st.extend([Spacer(1,13),P('Sector allocation','h2'),ExposureBars(report.get('sectorWeights',[])),Spacer(1,14),P('Strategy layer allocation','h2'),ExposureBars(report.get('layerWeights',[])),P('Issuer sector and layer classifications are indicative. ETF constituent look-through and revenue geography have not been independently reconstructed.','small')])
    st.append(PageBreak());section(st,3,'Return context & drawdown','Actual account return requires dated balances and net contributions. A price-weighted proxy cannot substitute for this data.')
    b=report.get('benchmarks',{})
    st.extend([MetricStrip([('PORTFOLIO 1W PROXY',pct(s.get('weekProxy'))),('S&P 500 ETF 1W',pct((b.get('spy') or {}).get('week'))),('NASDAQ-100 ETF 1W',pct((b.get('qqq') or {}).get('week')))]),Spacer(1,12),P('Performance interpretation','h2'),P('The portfolio and benchmark figures above are estimated using the latest quoted positions. Different constituent weights, timing of purchases, dividends, cash flows and currency movements can materially change actual results.'),P('Market stress indicators','h2')]);v=(b.get('vix') or {}).get('price');st.append(P(f"VIX: <b>{num(v)}</b> where available. VIX approximates 30-day expected equity-market volatility, <b>not</b> the CNN Fear & Greed Index or a mechanical entry signal."));st.append(P('Drawdown by holding (vs recent 52-week high)','h2'))
    dd=sorted([x for x in lines if x.get('fromHigh') is not None],key=lambda l:l['fromHigh'],reverse=True)
    st.extend(table(['TICKER','DISTANCE FROM 52W HIGH','CURRENT WEIGHT'],[[x['ticker'],f"-{num(x['fromHigh'])}%",num(x.get('weight'))+'%' if x.get('weight') is not None else 'N/A'] for x in dd[:15]],[100,229,W-329]));st.append(P('The 52-week-high distance is a price reference, not evidence of undervaluation, and does not by itself imply a buy or sell instruction.','small'))
    st.append(PageBreak());section(st,4,'Company & sector intelligence','Portfolio-relevant articles from recognized publications. News feed titles are not independent verification of an event.')
    company=[x for x in news if x.get('ticker')];sector=[x for x in news if x.get('category')=='Sector'];st.append(P('Company developments','h2'));st.extend(lines_of_items(company,8) or [P('No company-specific high-quality recent headline was available from the news feed.','small')]);st.append(P('Sector developments','h2'));st.extend(lines_of_items(sector,5) or [P('No qualifying sector article was retrieved.','small')]);st.append(P('Source standard','h3'));st.append(P('Use official company announcements, SEC filings, central-bank releases and primary regulator statements to substantiate each claimed impact before changing a thesis. Headlines are screening inputs only.','small'))
    st.append(PageBreak());section(st,5,'Macro, policy & geopolitical risk','Potential transmission channels to holdings are a research framework, not verified company-level exposure estimates.')
    macro=[x for x in news if not x.get('ticker') and x.get('category') not in ('Sector','Domicile')];st.extend(lines_of_items(macro,6) or [P('No qualifying macro or geopolitical headline was retrieved.','small')]);st.append(P('Risk transmission channels','h2'))
    st.extend(table(['EVENT','PORTFOLIO CHANNEL','WHAT TO VERIFY'],[['Rate decisions','Equity discount rates; debt refinancing; growth valuation','Central bank statement and yield curve'],['US export controls / Taiwan','Chip supply, foundry demand and equipment shipments','Official policy text, company exposure'],['Strait of Hormuz / energy','Oil, shipping insurance, supply chain and data-centre costs','Shipping data, supplier statements'],['Elections / fiscal policy','Taxes, subsidies, tariffs, procurement','Enacted laws and company filings'],['AI technology changes','Pricing power, capex intensity, obsolescence','Earnings guidance and product evidence']],[123,200,W-323]));st.append(P('Geographic coverage is based on issuer domicile. It does not replace a geographic revenue or production-location analysis.','small'))
    st.append(PageBreak());section(st,6,'Earnings & catalyst monitoring','Upcoming earnings dates are intentionally blank where no verified issuer or exchange calendar event is available.')
    earnings=report.get('earnings',[]);st.append(P('Recent earnings coverage','h2'));st.extend(lines_of_items(earnings,7) or [P('No recent qualifying earnings headline was retrieved.','small')]);st.append(P('Company calendar review','h2'))
    calendar=report.get('earningsCalendar',[]);st.extend(table(['SYMBOL','NEXT EVENT','SOURCE TO CHECK'],[[x.get('ticker'),'Date unverified','Issuer IR / Yahoo earnings calendar'] for x in calendar[:18]],[100,170,W-270]));st.append(P('A news article date is a publication date, not the earnings-call date. Confirm schedules with issuer Investor Relations before relying on them.','small'))
    st.append(PageBreak());section(st,7,'Research opportunities & decision log','Candidates for additional research, not orders. A buy rating requires verified financial evidence and a reproducible valuation.')
    ideas=report.get('ideas',[]);st.append(P('Watchlist review candidates','h2'));st.extend(table(['TICKER','PRIORITY','EVIDENCE STATUS'],[[x.get('ticker'),'High' if x.get('priority') else 'Standard','Fundamental diligence required'] for x in ideas[:14]],[112,95,W-207]));st.append(P('Research checklist','h2'))
    for t in ['Confirm last reported financial statements and official guidance (source and period).','Compare GAAP P/E, EV/EBITDA, P/FCF and ROIC against relevant peers with the same period.','Build bear, base and bull valuation cases; disclose cash-flow and discount assumptions.','Check diversification benefit, factor overlap, size limits and changes to the original thesis.','Review earnings calendar, capital allocation, insider activity and policy/geopolitical risks.']:
        st.append(P('• '+E(t),'body'))
    st.append(P('Methodology & limitations','h2'))
    for x in report.get('footnotes',[]):st.append(P('• '+E(x),'small'))
    st.append(P('News article source links appear with each item on pages 4–6. Primary documents are required before treating a headline as confirmed evidence.','small'))
    doc.build(st,onFirstPage=frame,onLaterPages=frame)
    return output.getvalue()
if __name__=='__main__':
    try:
        payload=json.load(sys.stdin);sys.stdout.buffer.write(build(payload))
    except Exception as e:
        print('PDF error: '+str(e),file=sys.stderr);sys.exit(2)
