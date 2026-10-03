import streamlit as st
import pymupdf
import base64

def mostrar_visor_pdf(pdf_bytes: bytes, nombre_archivo: str, label_boton: str = "📥 Descargar Reporte PDF Oficial"):
    """
    Renderiza de forma 100% compatible y nítida las páginas del PDF en pantalla
    y ofrece el botón oficial de descarga del documento.
    Evita los bloqueos de navegador (Chrome/Edge/Streamlit Cloud) con iframes data:base64.
    """
    st.markdown("#### 👁️ Vista Previa en Pantalla del Documento PDF Oficial:")
    
    # Contenedor visual estilizado
    with st.container():
        try:
            doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
            total_paginas = len(doc)
            
            for num_pag, pagina in enumerate(doc, start=1):
                pix = pagina.get_pixmap(dpi=150)
                img_bytes = pix.tobytes("png")
                
                if total_paginas > 1:
                    st.caption(f"📄 **Página {num_pag} de {total_paginas}**")
                
                st.image(img_bytes, use_container_width=True)
                
        except Exception as e:
            # Respaldo por iframe si ocurriera algún fallo inesperado
            b64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
            iframe_code = f'<iframe src="data:application/pdf;base64,{b64_pdf}" width="100%" height="650" type="application/pdf" style="border: 2px solid #0284c7; border-radius: 8px; margin-bottom: 15px;"></iframe>'
            st.markdown(iframe_code, unsafe_allow_html=True)

    st.download_button(
        label=label_boton,
        data=pdf_bytes,
        file_name=nombre_archivo,
        mime="application/pdf",
        use_container_width=True
    )
