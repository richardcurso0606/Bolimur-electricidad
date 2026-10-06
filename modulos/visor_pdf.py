import os
import streamlit as st
import pymupdf
import base64

def mostrar_visor_pdf(pdf_bytes: bytes, nombre_archivo: str, label_boton: str = "📥 Descargar Reporte PDF Oficial"):
    """
    Renderiza de forma 100% compatible y optimizada las páginas del PDF en pantalla
    y ofrece botones de descarga rápida del documento en la parte superior e inferior.
    Optimizado a 110 DPI para máxima velocidad y estabilidad en Streamlit Cloud.
    """
    safe_key = nombre_archivo.replace('.', '_').replace('-', '_').replace(' ', '_')

    col_btn, _ = st.columns([2, 1])
    with col_btn:
        st.download_button(
            label=label_boton,
            data=pdf_bytes,
            file_name=nombre_archivo,
            mime="application/pdf",
            type="primary",
            use_container_width=True,
            key=f"dl_top_{safe_key}"
        )

    st.markdown("#### 👁️ Vista Previa en Pantalla del Documento PDF Oficial:")
    
    with st.container():
        try:
            doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
            total_paginas = len(doc)
            
            for num_pag, pagina in enumerate(doc, start=1):
                pix = pagina.get_pixmap(dpi=110)
                img_bytes = pix.tobytes("png")
                
                if total_paginas > 1:
                    st.caption(f"📄 **Página {num_pag} de {total_paginas}**")
                
                st.image(img_bytes, use_container_width=True)
                
        except Exception:
            try:
                b64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
                iframe_code = f'<iframe src="data:application/pdf;base64,{b64_pdf}" width="100%" height="650" type="application/pdf" style="border: 2px solid #0284c7; border-radius: 8px; margin-bottom: 15px;"></iframe>'
                st.markdown(iframe_code, unsafe_allow_html=True)
            except Exception:
                pass

    st.download_button(
        label=label_boton,
        data=pdf_bytes,
        file_name=nombre_archivo,
        mime="application/pdf",
        type="primary",
        use_container_width=True,
        key=f"dl_bottom_{safe_key}"
    )
