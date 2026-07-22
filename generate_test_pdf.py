"""
generate_test_pdf.py
Generates a rich multi-modal test PDF covering:
  Text, Tables, Bar/Line/Pie/Scatter/Heatmap Charts,
  Images (embedded PNGs), Emojis, Math equations, Logo, Icons
"""

import io, os, sys, tempfile, atexit
sys.stdout.reconfigure(encoding="utf-8")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image as RLImage, HRFlowable, PageBreak,
)

W, H = A4
MARGIN = 2 * cm
USABLE_W = W - 2 * MARGIN   # ~481 pt = ~17 cm

# ── temp file tracker ─────────────────────────────────────────────────────────
_TMP = []
def _cleanup():
    for f in _TMP:
        try: os.remove(f)
        except: pass
atexit.register(_cleanup)

# ── chart helper ──────────────────────────────────────────────────────────────
def chart(fig, width_cm):
    """Save fig to temp file; return RLImage with explicit width+height."""
    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    tmp.close()
    fig.savefig(tmp.name, dpi=150, bbox_inches="tight", format="png")
    plt.close(fig)
    _TMP.append(tmp.name)
    # Read actual pixel size so we can give ReportLab both dimensions
    from PIL import Image as PILImg
    with PILImg.open(tmp.name) as pim:
        px_w, px_h = pim.size
    w_pt = width_cm * cm
    h_pt = w_pt * px_h / px_w
    img = RLImage(tmp.name, width=w_pt, height=h_pt)
    img.hAlign = "CENTER"
    return img

# ── colours & styles ──────────────────────────────────────────────────────────
C1, C2, C3 = "#1a1a2e", "#4F81BD", "#C0504D"
ss = getSampleStyleSheet()

def sty(name, **kw):
    return ParagraphStyle(name, parent=ss["Normal"], **kw)

TITLE   = sty("T",  fontSize=24, textColor=colors.HexColor(C1), alignment=TA_CENTER, spaceAfter=4, fontName="Helvetica-Bold")
SUBT    = sty("S",  fontSize=12, textColor=colors.HexColor(C2), alignment=TA_CENTER, spaceAfter=4)
H1      = sty("H1", fontSize=15, textColor=colors.HexColor(C1), spaceBefore=12, spaceAfter=5, fontName="Helvetica-Bold")
H2      = sty("H2", fontSize=12, textColor=colors.HexColor(C2), spaceBefore=8,  spaceAfter=4, fontName="Helvetica-Bold")
BODY    = sty("B",  fontSize=10, leading=15, spaceAfter=5, alignment=TA_JUSTIFY)
CODE    = sty("CD", fontSize=8,  leading=13, spaceAfter=7,
              backColor=colors.HexColor("#f4f4f4"),
              borderColor=colors.HexColor("#cccccc"),
              borderWidth=0.5, borderPad=5, fontName="Courier")
CAP     = sty("Ca", fontSize=8,  textColor=colors.grey, alignment=TA_CENTER, spaceAfter=8)
EMOJIP  = sty("E",  fontSize=10, leading=16, spaceAfter=4)

def tbl(data, widths, hdr=C2):
    t = Table(data, colWidths=widths)
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,0),  colors.HexColor(hdr)),
        ("TEXTCOLOR",     (0,0),(-1,0),  colors.white),
        ("FONTNAME",      (0,0),(-1,0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0,0),(-1,-1), 8.5),
        ("ROWBACKGROUNDS",(0,1),(-1,-1), [colors.HexColor("#f0f4ff"), colors.white]),
        ("GRID",          (0,0),(-1,-1), 0.4, colors.HexColor("#bbbbbb")),
        ("TOPPADDING",    (0,0),(-1,-1), 4),
        ("BOTTOMPADDING", (0,0),(-1,-1), 4),
        ("LEFTPADDING",   (0,0),(-1,-1), 5),
    ]))
    return t

# ── chart makers ──────────────────────────────────────────────────────────────

def logo():
    fig, ax = plt.subplots(figsize=(6, 1.8))
    ax.set_xlim(0,10); ax.set_ylim(0,3); ax.axis("off")
    ax.add_patch(mpatches.FancyBboxPatch((0.1,0.2),9.8,2.6,
        boxstyle="round,pad=0.1", facecolor=C1, edgecolor="none"))
    ax.add_patch(plt.Circle((1.3,1.5),0.75, color=C2))
    ax.text(1.3,1.5,"A",color="white",fontsize=18,fontweight="bold",ha="center",va="center")
    ax.text(2.7,1.85,"ACME AI Labs",color="white",fontsize=14,fontweight="bold",va="center")
    ax.text(2.7,0.9,"Intelligent Systems Division",color="#aaaaaa",fontsize=9,va="center")
    fig.patch.set_facecolor("none"); fig.tight_layout(pad=0)
    return chart(fig, 8)

def icons():
    lbs = ["Search","Analytics","AI","Config","Growth","Neural","Insight","Link","Package","Security","Global","Deploy"]
    cols = ["#4F81BD","#C0504D","#9BBB59","#8064A2","#4BACC6","#F79646"] * 2
    fig, ax = plt.subplots(figsize=(12, 1.8))
    ax.set_xlim(0,12); ax.set_ylim(0,1.6); ax.axis("off")
    for i,(lbl,col) in enumerate(zip(lbs,cols)):
        x = 0.5 + i
        ax.add_patch(mpatches.FancyBboxPatch((x-.42,.65),.84,.7,
            boxstyle="round,pad=0.05", facecolor=col, edgecolor="none", alpha=0.85))
        ax.text(x,.9+0.1, lbl[:3].upper(), fontsize=5.5, ha="center", va="center",
                color="white", fontweight="bold")
        ax.text(x,.38, lbl, fontsize=6, ha="center", va="center", color="#333")
    ax.set_title("System Capability Icons", fontsize=9, color="#444", pad=3)
    fig.tight_layout(pad=0)
    return chart(fig, 13)

def bar_chart():
    cats = ["Q1 2023","Q2 2023","Q3 2023","Q4 2023","Q1 2024"]
    rev  = [1.2,1.8,2.3,2.9,3.6]; cost = [0.8,1.1,1.4,1.7,2.0]
    x = np.arange(5)
    fig, ax = plt.subplots(figsize=(8,3.5))
    b1 = ax.bar(x-.2,rev,.38,label="Revenue ($M)",color=C2)
    b2 = ax.bar(x+.2,cost,.38,label="Costs ($M)",color=C3)
    for b in list(b1)+list(b2):
        ax.text(b.get_x()+b.get_width()/2, b.get_height()+.05,
                f"${b.get_height():.1f}M", ha="center", fontsize=8)
    ax.set_xticks(x); ax.set_xticklabels(cats,fontsize=8)
    ax.set_ylabel("USD Millions"); ax.set_ylim(0,4.5)
    ax.set_title("ACME AI Labs — Revenue vs Costs", fontweight="bold")
    ax.legend(fontsize=8); ax.grid(axis="y",ls="--",alpha=0.5)
    fig.tight_layout(); return chart(fig, 13)

def line_chart():
    months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    acc=[72,74,76,78,81,83,85,86,87,89,90,92]; lat=[340,330,320,310,295,280,265,255,245,235,228,220]
    fig, ax = plt.subplots(figsize=(8,3.5))
    ax2 = ax.twinx()
    ax.plot(months,acc,"o-",color=C2,lw=2,label="Accuracy (%)")
    ax2.plot(months,lat,"s--",color=C3,lw=2,label="Latency (ms)")
    ax.set_ylabel("Accuracy (%)"); ax2.set_ylabel("Latency (ms)")
    ax.set_ylim(60,100); ax2.set_ylim(180,380)
    ln = ax.get_legend_handles_labels()[0]+ax2.get_legend_handles_labels()[0]
    lb = ax.get_legend_handles_labels()[1]+ax2.get_legend_handles_labels()[1]
    ax.legend(ln,lb,loc="upper left",fontsize=8)
    ax.set_title("RAG Model — Accuracy & Latency 2024", fontweight="bold")
    ax.grid(ls="--",alpha=0.4)
    plt.xticks(fontsize=7); fig.tight_layout(); return chart(fig, 13)

def pie_chart():
    lbls=["Text","Tables","Images","Charts","Math/Code"]; szs=[45,20,15,12,8]
    pal=["#4F81BD","#C0504D","#9BBB59","#8064A2","#4BACC6"]
    fig, ax = plt.subplots(figsize=(5,4))
    ax.pie(szs,labels=lbls,autopct="%1.1f%%",startangle=140,
           colors=pal,explode=[0.05]*5,textprops={"fontsize":9})
    ax.set_title("Content-Type Distribution", fontweight="bold",fontsize=11)
    fig.tight_layout(); return chart(fig, 9)

def heatmap():
    mdls=["GPT-4o","Gemini 1.5","Claude 3","LLaMA 3"]
    mets=["Faithfulness","Relevancy","Precision","Recall"]
    data=np.array([[0.93,0.91,0.88,0.87],[0.90,0.89,0.86,0.84],
                   [0.91,0.88,0.85,0.83],[0.78,0.76,0.73,0.71]])
    fig, ax = plt.subplots(figsize=(6,3.5))
    im=ax.imshow(data,cmap="YlGn",vmin=0.6,vmax=1.0)
    ax.set_xticks(range(4)); ax.set_xticklabels(mets,fontsize=8)
    ax.set_yticks(range(4)); ax.set_yticklabels(mdls,fontsize=9)
    ax.set_title("RAGAS Scores by Model",fontweight="bold")
    for i in range(4):
        for j in range(4):
            ax.text(j,i,f"{data[i,j]:.2f}",ha="center",va="center",fontsize=10,
                    color="black" if data[i,j]<0.88 else "white")
    plt.colorbar(im,ax=ax,fraction=0.046,pad=0.04)
    fig.tight_layout(); return chart(fig, 11)

def scatter():
    cs=[128,256,512,750,1000,1500,2000,3000]
    ac=[0.71,0.78,0.85,0.88,0.91,0.89,0.86,0.80]
    fig, ax = plt.subplots(figsize=(7,3.5))
    ax.scatter(cs,ac,s=100,c=C2,edgecolors=C1,lw=1.5,zorder=5)
    z=np.polyfit(cs,ac,2); xs=np.linspace(128,3000,200)
    ax.plot(xs,np.poly1d(z)(xs),"r--",lw=1.5,alpha=0.7,label="Poly fit")
    ax.axvline(1000,ls=":",color="green",lw=1.5,label="Optimal")
    for c,a in zip(cs,ac): ax.annotate(str(c),(c,a+0.005),ha="center",fontsize=7.5)
    ax.set_xlabel("Chunk Size (tokens)"); ax.set_ylabel("RAGAS Recall@5")
    ax.set_title("Chunk Size vs Retrieval Accuracy",fontweight="bold")
    ax.legend(fontsize=8); ax.grid(ls="--",alpha=0.4)
    fig.tight_layout(); return chart(fig, 11)

def pipeline_diagram():
    stages=[("PDF\nInput",C2),("Extract\n(multi)",  "#9BBB59"),
            ("Chunk\n+Embed","#C0504D"),("Vector\nStore","#8064A2"),
            ("MMR\nRetrieve","#4BACC6"),("LLM\nGenerate","#F79646"),
            ("JSON\nAnswer", C2)]
    fig, ax = plt.subplots(figsize=(11,3))
    ax.set_xlim(0,11); ax.set_ylim(0,3); ax.axis("off")
    for i,(lbl,col) in enumerate(stages):
        x = 0.65+i*1.55
        ax.add_patch(mpatches.FancyBboxPatch((x-.62,.55),1.24,1.9,
            boxstyle="round,pad=0.07",facecolor=col,edgecolor="white",lw=1.5))
        ax.text(x,1.5,lbl,ha="center",va="center",fontsize=8,color="white",fontweight="bold")
        if i<len(stages)-1:
            ax.annotate("",xy=(x+0.73,1.5),xytext=(x+0.62,1.5),
                        arrowprops=dict(arrowstyle="->",color="#555",lw=1.8))
    ax.set_title("End-to-End RAG Pipeline",fontsize=12,fontweight="bold",pad=6)
    fig.tight_layout(); return chart(fig, 13)

# ── build ─────────────────────────────────────────────────────────────────────

def add_header(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica-Bold", 8)
    canvas.setFillColor(colors.HexColor(C2))
    canvas.drawString(MARGIN, H-1.4*cm, "ACME AI Labs — Enterprise RAG Technical Report")
    canvas.setFillColor(colors.grey)
    canvas.drawRightString(W-MARGIN, H-1.4*cm, f"Page {doc.page}")
    canvas.setStrokeColor(colors.HexColor(C2))
    canvas.setLineWidth(0.5)
    canvas.line(MARGIN, H-1.6*cm, W-MARGIN, H-1.6*cm)
    canvas.restoreState()


def build_pdf(out: str):
    doc = SimpleDocTemplate(out, pagesize=A4,
                            leftMargin=MARGIN, rightMargin=MARGIN,
                            topMargin=2.2*cm, bottomMargin=2*cm,
                            onFirstPage=add_header, onLaterPages=add_header)
    s = []   # story

    # ── COVER ────────────────────────────────────────────────────────────────
    s += [Spacer(1,2*cm), logo(), Spacer(1,.8*cm),
          Paragraph("Enterprise AI & RAG Technical Report", TITLE),
          Paragraph("Multi-Modal Document Intelligence Platform v2.4.1", SUBT),
          Spacer(1,.4*cm),
          HRFlowable(width="80%",thickness=1.5,color=colors.HexColor(C2),hAlign="CENTER"),
          Spacer(1,.5*cm)]
    cover = [["Version","2.4.1"],["Classification","Internal — Confidential"],
             ["Author","ACME AI Labs Research Team"],["Date","July 2024"],
             ["Dept","Intelligent Systems Division"]]
    ct = Table(cover, colWidths=[4*cm, 9*cm])
    ct.setStyle(TableStyle([
        ("FONTNAME",(0,0),(0,-1),"Helvetica-Bold"),("FONTSIZE",(0,0),(-1,-1),10),
        ("ROWBACKGROUNDS",(0,0),(-1,-1),[colors.HexColor("#f0f4ff"),colors.white]),
        ("GRID",(0,0),(-1,-1),0.4,colors.HexColor("#ccc")),
        ("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5),
        ("LEFTPADDING",(0,0),(-1,-1),8),
    ]))
    ct.hAlign = "CENTER"
    s += [ct, PageBreak()]

    # ── 1. EXECUTIVE SUMMARY (text + emojis) ─────────────────────────────────
    s += [Paragraph("1. Executive Summary", H1),
          Paragraph("This report presents the architecture, benchmarks, and evaluation "
                    "results of ACME AI Labs' Retrieval-Augmented Generation (RAG) platform "
                    "designed for complex enterprise PDF corpora containing text, structured "
                    "tables, raster images, charts, mathematical notation, and emoji sequences.",
                    BODY),
          Paragraph("Key Highlights  \U0001f3c6", H2)]
    for h in [
        "\U0001f680  Ingestion pipeline processes <b>500+ page PDFs</b> in under 90 seconds.",
        "\U0001f3af  RAGAS Faithfulness score of <b>0.93</b> on the internal benchmark.",
        "\U0001f4ca  <b>5 content-type extractors</b>: text, tables, images, math, emojis.",
        "\u26a1  P95 query latency of <b>220 ms</b> with Gemini 1.5 Flash.",
        "\U0001f512  Fully on-premise deployment via <b>Ollama + ChromaDB</b>.",
        "\U0001f30d  Supports <b>12 languages</b> with multilingual embeddings.",
        "\u2705  Zero-shot accuracy of <b>87%</b> on unseen enterprise PDF test sets.",
    ]:
        s.append(Paragraph(h, EMOJIP))
    s += [Spacer(1,.3*cm),
          Paragraph("Emoji Test: \U0001f600 \U0001f50d \U0001f4c8 \U0001f4a1 \u2699\ufe0f "
                    "\U0001f916 \U0001f9e0 \U0001f517 \U0001f4e6 \U0001f6e1\ufe0f "
                    "\U0001f310 \U0001f389 \u2728 \U0001f3d7\ufe0f \U0001f52c \U0001f4dd", EMOJIP),
          Spacer(1,.3*cm),
          Paragraph("System Capability Icons", H2),
          icons(),
          Paragraph("Figure 1 - Core system capabilities at a glance.", CAP),
          PageBreak()]

    # ── 2. ARCHITECTURE ───────────────────────────────────────────────────────
    s += [Paragraph("2. System Architecture", H1),
          Paragraph("The RAG platform follows a modular pipeline design. Each stage is "
                    "independently configurable via environment variables, enabling seamless "
                    "switching between cloud and on-premise providers without code changes.", BODY),
          Paragraph("2.1  Pipeline Stages", H2)]
    s.append(tbl([
        ["Stage","Component","Technology Options"],
        ["1. Ingestion",  "PDF Parser",       "PyMuPDF, pdfplumber, Unstructured"],
        ["2. Extraction", "Content Extractor", "Text, Tables, Images, Math, Emojis"],
        ["3. Embedding",  "Vector Encoding",   "sentence-transformers, Gemini Embed"],
        ["4. Storage",    "Vector Store",      "ChromaDB (local), Pinecone (cloud)"],
        ["5. Retrieval",  "Retriever",         "MMR, BM25 Hybrid, Re-ranker"],
        ["6. Generation", "LLM",              "Gemini 1.5 Flash, Ollama LLaMA 3"],
        ["7. Evaluation", "RAGAS",             "Faithfulness, Relevancy, Precision"],
    ], [3.5*cm,4*cm,7.5*cm], hdr=C1))
    s += [Spacer(1,.4*cm),
          Paragraph("2.2  .env Configuration", H2),
          Paragraph("All runtime choices are set in a single <b>.env</b> file:", BODY),
          Paragraph("LLM_PROVIDER=gemini          # gemini | ollama<br/>"
                    "VECTOR_STORE=chromadb        # chromadb | pinecone<br/>"
                    "EMBEDDING_PROVIDER=local     # local | gemini<br/>"
                    "CHUNK_SIZE=1000<br/>"
                    "CHUNK_OVERLAP=200<br/>"
                    "GEMINI_API_KEY=AIza...<br/>"
                    "PINECONE_API_KEY=pcsk_...", CODE),
          Paragraph("2.3  Pipeline Diagram", H2),
          pipeline_diagram(),
          Paragraph("Figure 2 - End-to-end RAG pipeline from PDF input to JSON answer.", CAP),
          PageBreak()]

    # ── 3. CHARTS ─────────────────────────────────────────────────────────────
    s += [Paragraph("3. Performance Benchmarks", H1),
          Paragraph("3.1  Revenue vs Costs - Bar Chart", H2),
          Paragraph("Quarterly revenue versus costs as the platform scaled from pilot to production.",BODY),
          bar_chart(),
          Paragraph("Figure 3 - Quarterly Revenue vs Costs (USD Millions).", CAP),
          Spacer(1,.2*cm),
          Paragraph("3.2  Accuracy & Latency Trend - Line Chart", H2),
          Paragraph("Accuracy improved +20pts while latency fell 35% through quantisation and caching.",BODY),
          line_chart(),
          Paragraph("Figure 4 - RAG model accuracy and latency over 2024.", CAP),
          PageBreak(),
          Paragraph("3.3  Content-Type Distribution - Pie Chart", H2),
          Paragraph("Analysis of 10,000 enterprise PDF pages. Non-text content accounts for "
                    "55% of information density and carries the highest business value.", BODY),
          pie_chart(),
          Paragraph("Figure 5 - Content-type distribution across enterprise document corpus.", CAP),
          Spacer(1,.3*cm),
          Paragraph("3.4  RAGAS Evaluation Heatmap", H2),
          Paragraph("Four LLMs evaluated across four RAGAS metrics. GPT-4o leads; "
                    "Gemini 1.5 Flash offers best cost-performance ratio.", BODY),
          heatmap(),
          Paragraph("Figure 6 - RAGAS evaluation heatmap (green = better).", CAP),
          PageBreak(),
          Paragraph("3.5  Chunk Size vs Accuracy - Scatter Plot", H2),
          Paragraph("Optimal chunk size is ~1,000 tokens. Smaller chunks lose context; "
                    "larger chunks introduce retrieval noise.", BODY),
          scatter(),
          Paragraph("Figure 7 - Chunk size (tokens) vs RAGAS Recall@5.", CAP),
          PageBreak()]

    # ── 4. MATH EQUATIONS ────────────────────────────────────────────────────
    s += [Paragraph("4. Mathematical Foundations", H1),
          Paragraph("4.1  Cosine Similarity (Dense Retrieval)", H2),
          Paragraph("For embedding vectors <b>A</b> and <b>B</b> in R<sup>d</sup>:", BODY),
          Paragraph("cos(theta) = (A . B) / (||A|| x ||B||) = Sum_i(A_i*B_i) / sqrt(Sum_i A_i^2) x sqrt(Sum_i B_i^2)", CODE),
          Paragraph("cos(theta) in [-1,1]. After L2 normalisation it reduces to a dot product.", BODY),
          Paragraph("4.2  BM25 Sparse Retrieval", H2),
          Paragraph("BM25 score for document D and query Q:", BODY),
          Paragraph("BM25(D,Q) = Sum_{t in Q}  IDF(t) * [ f(t,D)*(k1+1) ] / [ f(t,D) + k1*(1 - b + b*|D|/avgdl) ]", CODE),
          Paragraph("k1=1.5 (term frequency saturation), b=0.75 (length normalisation).", BODY),
          Paragraph("4.3  Reciprocal Rank Fusion", H2),
          Paragraph("RRF(d) = Sum_{k in rankings}  1 / (60 + rank_k(d))", CODE),
          Paragraph("4.4  RAGAS Faithfulness", H2),
          Paragraph("F = |{ c in claims(A) : c entails C }| / |claims(A)|", CODE),
          Paragraph("F=1.0 means every generated claim is supported by retrieved context.", BODY),
          Paragraph("4.5  Transformer Self-Attention", H2),
          Paragraph("Attention(Q, K, V) = softmax( Q*K^T / sqrt(d_k) ) * V", CODE),
          Paragraph("MultiHead(Q,K,V) = Concat(head_1, ..., head_h) * W^O", CODE),
          Paragraph("For GPT-4: d_k=128, h=96 heads.  sqrt(128) = 11.31", BODY),
          Paragraph("4.6  Shannon Entropy for Retrieval Diversity", H2),
          Paragraph("H(X) = -Sum_i p(x_i) * log2(p(x_i))", CODE),
          Paragraph("Higher H means more diverse retrieved chunks, reducing hallucination risk.", BODY),
          PageBreak()]

    # ── 5. TABLES ─────────────────────────────────────────────────────────────
    s += [Paragraph("5. Benchmark Data Tables", H1),
          Paragraph("5.1  Embedding Model Comparison", H2)]
    s.append(tbl([
        ["Model","Dims","Recall@5","Latency","Cost/1M","License"],
        ["text-embedding-3-large","3072","96.1%","320ms","$0.13","OpenAI"],
        ["text-embedding-3-small","1536","92.3%","180ms","$0.02","OpenAI"],
        ["all-MiniLM-L6-v2",     "384", "84.7%","12ms", "Free", "Apache 2.0"],
        ["BAAI/bge-large-en-v1.5","1024","93.8%","48ms","Free", "MIT"],
        ["Gemini text-embed-004", "768", "94.2%","95ms", "$0.00","Google"],
        ["nomic-embed-text-v1.5", "768", "91.5%","22ms", "Free", "Apache 2.0"],
    ], [5*cm,1.5*cm,2*cm,2*cm,2.3*cm,3*cm]))
    s += [Spacer(1,.4*cm), Paragraph("5.2  LLM Provider Comparison", H2)]
    s.append(tbl([
        ["Model","Context","RAG Score","P95 Lat","Vision","$/1M out"],
        ["GPT-4o",              "128k","0.93","420ms","\u2705","$15.00"],
        ["Gemini 1.5 Flash",    "1M",  "0.90","220ms","\u2705","$0.53"],
        ["Gemini 1.5 Pro",      "1M",  "0.92","580ms","\u2705","$3.50"],
        ["Claude 3 Sonnet",     "200k","0.91","390ms","\u2705","$15.00"],
        ["LLaMA 3 70B (Ollama)","8k",  "0.82","1800ms","\u274c","Free"],
        ["LLaVA 13B (Ollama)",  "4k",  "0.74","2200ms","\u2705","Free"],
    ], [5*cm,1.8*cm,2.2*cm,2*cm,1.5*cm,3.3*cm], hdr=C1))
    s += [Spacer(1,.4*cm), Paragraph("5.3  Vector Store Comparison", H2)]
    s.append(tbl([
        ["Store","Type","Max Vecs","Latency","Persist","Cost"],
        ["ChromaDB","Local",    "~10M",   "2-5ms",  "\u2705 Files","Free"],
        ["FAISS",   "Memory",   "Unlim.", "1-3ms",  "\u26a0 Manual","Free"],
        ["Pinecone","Cloud",    "Unlim.", "20-40ms", "\u2705 Cloud","$0.096/unit"],
        ["Qdrant",  "Cloud/Self","Unlim.","5-15ms",  "\u2705","Free/paid"],
    ], [3*cm,2.2*cm,2.5*cm,2.2*cm,2.5*cm,3.4*cm]))
    s.append(PageBreak())

    # ── 6. EMOJI & SPECIAL CHARACTERS ─────────────────────────────────────────
    s += [Paragraph("6. Emoji & Special Character Handling", H1),
          Paragraph("Enterprise documents use emoji sequences in dashboards and executive "
                    "summaries. The RAG pipeline preserves all UTF-8 code points through "
                    "extraction, chunking, embedding, and retrieval.", BODY),
          Paragraph("6.1  System Status Dashboard", H2)]
    s.append(tbl([
        ["Component",          "Status",          "Health",      "Notes"],
        ["PDF Ingestion",       "\u2705 Live",     "\U0001f7e2 100%","All content types"],
        ["Text Extractor",      "\u2705 Live",     "\U0001f7e2 99.8%","UTF-8 + emoji"],
        ["Table Extractor",     "\u2705 Live",     "\U0001f7e2 98.3%","Markdown output"],
        ["Image Extractor",     "\u2705 Live",     "\U0001f7e1 95.1%","Vision LLM warm-up"],
        ["Math Extractor",      "\u2705 Live",     "\U0001f7e2 97.6%","LaTeX + plain-text"],
        ["ChromaDB Store",      "\u2705 Live",     "\U0001f7e2 100%", "2.1M vectors"],
        ["Pinecone Store",      "\u2705 Live",     "\U0001f7e2 100%", "50M capacity"],
        ["Gemini 1.5 Flash",    "\u2705 Live",     "\U0001f7e2 99.9%","220ms P95"],
        ["Ollama (local)",      "\u23f8 Standby",  "\U0001f7e1 N/A",  "Pull llava first"],
        ["RAGAS Evaluator",     "\u2705 Live",     "\U0001f7e2 100%", "F=0.93"],
        ["FastAPI Server",      "\u2705 Live",     "\U0001f7e2 100%", "3 endpoints"],
    ], [4.5*cm,2.5*cm,2.3*cm,6.5*cm], hdr=C1))
    s += [Spacer(1,.4*cm), Paragraph("6.2  Emoji Category Coverage", H2)]
    cats = [
        ("Smileys",   "\U0001f600 \U0001f603 \U0001f604 \U0001f601 \U0001f606 \U0001f923 \U0001f602 \U0001f642 \U0001f609 \U0001f60a \U0001f970 \U0001f60d"),
        ("Status",    "\u2705 \u274c \u26a0\ufe0f \U0001f534 \U0001f7e1 \U0001f7e2 \u23f8 \u25b6\ufe0f \u23e9 \U0001f514 \U0001f4cc \U0001f4cd"),
        ("Tech",      "\U0001f4bb \U0001f5a5\ufe0f \U0001f4f1 \u2328\ufe0f \U0001f50c \U0001f50b \U0001f4be \U0001f4e1 \U0001f6f0\ufe0f \U0001f52d"),
        ("Analytics", "\U0001f4ca \U0001f4c8 \U0001f4c9 \U0001f4cb \U0001f4c1 \U0001f4dd \u270f\ufe0f \U0001f4d0 \U0001f4cf \U0001f522"),
        ("Science",   "\U0001f52c \U0001f9ec \U0001f9ea \u2697\ufe0f \U0001f321\ufe0f \U0001f9f2 \U0001f48a \U0001f680 \U0001f6f8"),
        ("Math Syms", "\u03a3 \u222b \u221a \u03c0 \u03b1 \u03b2 \u03b3 \u03b8 \u03bb \u03bc \u03c3 \u2202 \u2207 \u221e \u2248 \u2260 \u2264 \u2265"),
        ("Flags",     "\U0001f1fa\U0001f1f8 \U0001f1ec\U0001f1e7 \U0001f1e9\U0001f1ea \U0001f1eb\U0001f1f7 \U0001f1ef\U0001f1f5 \U0001f1e8\U0001f1f3 \U0001f1ee\U0001f1f3 \U0001f30d \U0001f30e \U0001f30f"),
    ]
    for cat, emojis in cats:
        s.append(Paragraph(f"<b>{cat}:</b>  {emojis}", EMOJIP))
    s.append(PageBreak())

    # ── 7. CONCLUSION ─────────────────────────────────────────────────────────
    s += [Paragraph("7. Conclusion & Next Steps", H1),
          Paragraph("The ACME AI Labs RAG platform demonstrates state-of-the-art performance "
                    "on multi-modal enterprise PDF documents. With configurable LLM and vector "
                    "store backends, the system adapts to both fully local on-premise deployments "
                    "and cloud-scale production environments without any code changes.", BODY),
          Paragraph("Next Steps  \U0001f5fa\ufe0f", H2)]
    for step in [
        "\U0001f527  Integrate <b>re-ranking</b> with Cohere Rerank or FlashRank (+3% precision).",
        "\U0001f5bc\ufe0f  Expand vision pipeline for <b>multi-page chart understanding</b>.",
        "\U0001f310  Add <b>multilingual retrieval</b> with mE5-large embeddings.",
        "\U0001f4ca  Build a <b>Streamlit evaluation dashboard</b> for real-time RAGAS monitoring.",
        "\U0001f512  Implement <b>PII redaction</b> before vector storage for compliance.",
        "\u26a1  Deploy <b>async ingestion queue</b> (Celery + Redis) for large batch jobs.",
        "\U0001f9ea  Expand test suite with <b>100 Q&A pairs</b> across all content types.",
    ]:
        s.append(Paragraph(step, EMOJIP))
    s += [Spacer(1,.8*cm),
          HRFlowable(width="100%",thickness=1,color=colors.HexColor(C2)),
          Spacer(1,.3*cm),
          Paragraph("(c) 2024 ACME AI Labs — Intelligent Systems Division<br/>"
                    "Generated for RAG pipeline testing purposes.<br/>"
                    "Contains: Text | Tables | Charts | Images | Emojis | Math | Logos | Icons",
                    CAP)]

    print(f"Building -> {out}")
    doc.build(s)
    kb = os.path.getsize(out)/1024
    print(f"Done! {kb:.0f} KB | Sections: Text, Tables(3), Charts(5 types), Math(6 eq), Emojis(100+), Logo, Icons")


if __name__ == "__main__":
    out = r"a:\Github Repos\Rag-pdf\Rag-pdf\RAG_Test_Document_MultiModal.pdf"
    build_pdf(out)
