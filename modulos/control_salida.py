# -*- coding: utf-8 -*-
"""
Módulo de Control de Salida y Protección contra Cierre Accidental (Tecla Escape y Navegador)
Bolimur REBT PRO

Impide que la aplicación se cierre involuntariamente al presionar la tecla Escape (Esc)
o al intentar cerrar la pestaña o ventana del navegador sin confirmación explícita del usuario.
"""

import streamlit as st
import streamlit.components.v1 as components

def inyectar_control_escape():
    """
    Inyecta el script y modal en el DOM del navegador (ventana padre) para:
    1. Interceptar la tecla Escape a nivel global e impedir cualquier cierre no autorizado.
    2. Mostrar un diálogo modal de confirmación con diseño Bolimur pidiendo confirmación.
    3. Proteger la pestaña con beforeunload ante cierres accidentales.
    """
    codigo_html = """
    <script>
    (function() {
        // Obtener la ventana principal (parent o top) de Streamlit
        var targetWin = window;
        var targetDoc = document;
        try {
            if (window.parent && window.parent.document) {
                targetWin = window.parent;
                targetDoc = window.parent.document;
            }
        } catch (e) {
            targetWin = window;
            targetDoc = document;
        }

        // 1. Protección contra cierre accidental de pestaña/ventana (beforeunload)
        if (!targetWin.__bolimur_beforeunload_active) {
            targetWin.__bolimur_allow_exit = false;
            targetWin.addEventListener('beforeunload', function(e) {
                if (targetWin.__bolimur_allow_exit) {
                    return undefined;
                }
                var mensaje = '¿Estás seguro de que deseas salir de Bolimur REBT? Es posible que los datos no guardados se pierdan.';
                e.preventDefault();
                e.returnValue = mensaje;
                return mensaje;
            });
            targetWin.__bolimur_beforeunload_active = true;
        }

        // 2. Intentar bloquear la tecla Escape si el navegador está en pantalla completa
        try {
            if (targetDoc.fullscreenElement && targetWin.navigator && targetWin.navigator.keyboard && targetWin.navigator.keyboard.lock) {
                targetWin.navigator.keyboard.lock(['Escape']);
            }
        } catch (err) {}

        // 3. Crear el Modal de Confirmación en el Documento Principal si no existe
        var modalId = 'bolimur-exit-confirm-modal';
        var modalExistente = targetDoc.getElementById(modalId);

        if (!modalExistente) {
            var modal = targetDoc.createElement('div');
            modal.id = modalId;
            modal.style.cssText = [
                'display: none',
                'position: fixed',
                'top: 0',
                'left: 0',
                'width: 100vw',
                'height: 100vh',
                'background: rgba(15, 23, 42, 0.75)',
                'backdrop-filter: blur(5px)',
                '-webkit-backdrop-filter: blur(5px)',
                'z-index: 2147483647',
                'align-items: center',
                'justify-content: center',
                'font-family: system-ui, -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif',
                'box-sizing: border-box',
                'opacity: 0',
                'transition: opacity 0.2s ease-in-out'
            ].join(' !important;') + ' !important;';

            modal.innerHTML = `
                <div id="bolimur-modal-box" style="
                    background: #ffffff !important;
                    border: 2px solid #0284c7 !important;
                    border-radius: 16px !important;
                    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5) !important;
                    width: 90% !important;
                    max-width: 490px !important;
                    padding: 26px 24px !important;
                    text-align: center !important;
                    box-sizing: border-box !important;
                    transform: scale(0.92) !important;
                    transition: transform 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
                ">
                    <div style="
                        width: 58px !important;
                        height: 58px !important;
                        background: #fffbeb !important;
                        border: 2px solid #fde68a !important;
                        border-radius: 50% !important;
                        display: flex !important;
                        align-items: center !important;
                        justify-content: center !important;
                        margin: 0 auto 16px auto !important;
                        font-size: 28px !important;
                    ">
                        ⚠️
                    </div>

                    <div style="font-size: 11px !important; font-weight: 700 !important; color: #0284c7 !important; text-transform: uppercase !important; letter-spacing: 0.05em !important; margin-bottom: 6px !important;">
                        ⚡ Bolimur REBT PRO • Control de Salida
                    </div>

                    <h3 style="
                        margin: 0 0 10px 0 !important;
                        color: #0f172a !important;
                        font-size: 20px !important;
                        font-weight: 700 !important;
                    ">¿Deseas salir de la aplicación?</h3>

                    <p style="
                        margin: 0 0 22px 0 !important;
                        color: #475569 !important;
                        font-size: 14px !important;
                        line-height: 1.55 !important;
                    ">
                        Has pulsado la tecla <strong>Escape</strong>.<br>
                        Para evitar cierres accidentales o pérdida de cálculos técnicos, debes <strong>confirmar</strong> si realmente deseas salir.
                    </p>

                    <div style="
                        display: flex !important;
                        gap: 12px !important;
                        justify-content: center !important;
                    ">
                        <button id="bolimur-btn-permanecer" type="button" style="
                            flex: 1.2 !important;
                            background: #0284c7 !important;
                            color: #ffffff !important;
                            border: none !important;
                            padding: 12px 16px !important;
                            border-radius: 10px !important;
                            font-size: 14px !important;
                            font-weight: 600 !important;
                            cursor: pointer !important;
                            box-shadow: 0 4px 10px rgba(2, 132, 199, 0.3) !important;
                            transition: background 0.15s ease !important;
                        ">🛡️ Permanecer aquí</button>

                        <button id="bolimur-btn-salir" type="button" style="
                            flex: 0.9 !important;
                            background: #fef2f2 !important;
                            color: #dc2626 !important;
                            border: 1.5px solid #f87171 !important;
                            padding: 12px 14px !important;
                            border-radius: 10px !important;
                            font-size: 14px !important;
                            font-weight: 600 !important;
                            cursor: pointer !important;
                            transition: background 0.15s ease !important;
                        ">🚪 Sí, salir</button>
                    </div>

                    <div style="margin-top: 14px !important; font-size: 12px !important; color: #94a3b8 !important;">
                        Si pulsas <em>Permanecer</em> o haces clic fuera, seguirás dentro sin perder nada.
                    </div>
                </div>
            `;

            targetDoc.body.appendChild(modal);

            function abrirModal() {
                modal.style.display = 'flex';
                setTimeout(function() {
                    modal.style.opacity = '1';
                    var card = targetDoc.getElementById('bolimur-modal-box');
                    if (card) card.style.transform = 'scale(1)';
                    var btnPermanecer = targetDoc.getElementById('bolimur-btn-permanecer');
                    if (btnPermanecer) btnPermanecer.focus();
                }, 10);
                targetWin.__bolimur_modal_visible = true;
            }

            function cerrarModal() {
                modal.style.opacity = '0';
                var card = targetDoc.getElementById('bolimur-modal-box');
                if (card) card.style.transform = 'scale(0.92)';
                setTimeout(function() {
                    modal.style.display = 'none';
                }, 200);
                targetWin.__bolimur_modal_visible = false;
            }

            targetWin.__bolimur_abrir_modal = abrirModal;
            targetWin.__bolimur_cerrar_modal = cerrarModal;

            // Botón Permanecer
            var btnStay = targetDoc.getElementById('bolimur-btn-permanecer');
            if (btnStay) {
                btnStay.addEventListener('click', function(ev) {
                    ev.preventDefault();
                    ev.stopPropagation();
                    cerrarModal();
                });
                btnStay.addEventListener('mouseenter', function() {
                    btnStay.style.background = '#0369a1';
                });
                btnStay.addEventListener('mouseleave', function() {
                    btnStay.style.background = '#0284c7';
                });
            }

            // Botón Salir
            var btnExit = targetDoc.getElementById('bolimur-btn-salir');
            if (btnExit) {
                btnExit.addEventListener('click', function(ev) {
                    ev.preventDefault();
                    ev.stopPropagation();
                    targetWin.__bolimur_allow_exit = true;
                    cerrarModal();

                    // 1. Intentar cerrar la ventana del navegador
                    try {
                        targetWin.close();
                    } catch (err) {}

                    // 2. Si el navegador no permite cerrar la ventana (por seguridad), redirigir o cerrar sesión
                    setTimeout(function() {
                        var baseUrl = targetWin.location.pathname || '/';
                        targetWin.location.href = baseUrl + '?salir=1';
                    }, 200);
                });
                btnExit.addEventListener('mouseenter', function() {
                    btnExit.style.background = '#fee2e2';
                });
                btnExit.addEventListener('mouseleave', function() {
                    btnExit.style.background = '#fef2f2';
                });
            }

            // Clic fuera del recuadro cierra el modal (permanece en la app)
            modal.addEventListener('click', function(ev) {
                if (ev.target === modal) {
                    cerrarModal();
                }
            });
        }

        // 4. Interceptor universal de la tecla Escape
        function onKeyDownEscape(e) {
            var esEscape = (e.key === 'Escape' || e.key === 'Esc' || e.keyCode === 27 || e.code === 'Escape');
            if (esEscape) {
                // Si el modal de confirmación ya está visible, pulsar Escape lo cierra (permanecer en la app)
                if (targetWin.__bolimur_modal_visible) {
                    e.preventDefault();
                    e.stopPropagation();
                    e.stopImmediatePropagation();
                    if (typeof targetWin.__bolimur_cerrar_modal === 'function') {
                        targetWin.__bolimur_cerrar_modal();
                    }
                    return false;
                }

                // Si hay un desplegable de selección abierto en Streamlit, permitir que Escape lo cierre normalmente
                try {
                    var openDropdown = targetDoc.querySelector('div[data-baseweb="popover"], div[role="listbox"], ul[role="listbox"]');
                    if (openDropdown && openDropdown.offsetParent !== null) {
                        return; // Dejar que el desplegable se repliegue sin alertar de salida
                    }
                } catch(err) {}

                // Detener cualquier acción predeterminada de Escape (cerrar app, salir de pantalla completa, etc.)
                e.preventDefault();
                e.stopPropagation();
                e.stopImmediatePropagation();

                // Mostrar aviso modal pidiendo confirmación explícita para salir
                if (typeof targetWin.__bolimur_abrir_modal === 'function') {
                    targetWin.__bolimur_abrir_modal();
                }
                return false;
            }
        }

        // Instalar listeners con useCapture = true para tener máxima prioridad
        if (!targetWin.__bolimur_esc_listener_installed) {
            targetWin.addEventListener('keydown', onKeyDownEscape, true);
            targetWin.addEventListener('keyup', function(e) {
                if (e.key === 'Escape' || e.keyCode === 27) {
                    e.preventDefault();
                    e.stopPropagation();
                    e.stopImmediatePropagation();
                }
            }, true);
            targetDoc.addEventListener('keydown', onKeyDownEscape, true);

            // Escuchar también en el iframe local por si el foco está dentro de un widget
            try {
                window.addEventListener('keydown', onKeyDownEscape, true);
                document.addEventListener('keydown', onKeyDownEscape, true);
            } catch(e) {}

            targetWin.__bolimur_esc_listener_installed = true;
        }

        // 5. Interceptar Botón Atrás y Gesto de Deslizar Atrás en Móviles / Tablets (popstate)
        function instalarControlAtrasMovil() {
            if (targetWin.__bolimur_popstate_installed) return;

            // Empujar un estado al historial del navegador para capturar el primer toque de Atrás
            try {
                targetWin.history.pushState({ bolimur: true }, '', targetWin.location.href);
            } catch(e) {}

            targetWin.addEventListener('popstate', function(ev) {
                if (targetWin.__bolimur_allow_exit) {
                    return; // Si el usuario confirmó salir, permitir navegación
                }

                // Restaurar el estado en el historial para evitar que el navegador cierre la pestaña o vuelva a la página anterior
                try {
                    targetWin.history.pushState({ bolimur: true }, '', targetWin.location.href);
                } catch(e) {}

                // Si el modal de confirmación ya está visible, cerrarlo (permanecer en la app)
                if (targetWin.__bolimur_modal_visible) {
                    if (typeof targetWin.__bolimur_cerrar_modal === 'function') {
                        targetWin.__bolimur_cerrar_modal();
                    }
                    return;
                }

                // En móvil: si el menú lateral está abierto, cerrarlo primero (comportamiento estándar de app nativa)
                try {
                    var sidebar = targetDoc.querySelector('[data-testid="stSidebar"]');
                    var btnCollapse = targetDoc.querySelector(
                        '[data-testid="stSidebarCollapseButton"] button, ' +
                        '[data-testid="stSidebarCollapseButton"], ' +
                        'button[aria-label="Collapse sidebar"]'
                    );
                    if (sidebar && sidebar.getAttribute('aria-expanded') !== 'false' && btnCollapse && targetWin.innerWidth < 992) {
                        btnCollapse.click();
                        return;
                    }
                } catch(err) {}

                // Si no hay menú lateral abierto, mostrar el aviso modal de confirmación de salida
                if (typeof targetWin.__bolimur_abrir_modal === 'function') {
                    targetWin.__bolimur_abrir_modal();
                }
            }, false);

            targetWin.__bolimur_popstate_installed = true;
        }

        instalarControlAtrasMovil();

        // 6. Desplazar/desaparecer la barra lateral izquierda al pulsar en la ventana derecha (aplicación)
        function instalarAutoColapsoSidebar() {
            if (targetWin.__bolimur_sidebar_click_installed) return;

            function onVentanaDerechaClick(e) {
                try {
                    var sidebar = targetDoc.querySelector('[data-testid="stSidebar"]');
                    if (!sidebar) return;

                    // Si el clic fue dentro de la barra lateral, no colapsar (el usuario interactúa con el menú)
                    if (sidebar.contains(e.target)) {
                        return;
                    }

                    // Si el clic fue en el botón de expandir la barra lateral, permitir que se expanda
                    var btnExpand = targetDoc.querySelector('[data-testid="stExpandSidebarButton"]');
                    if (btnExpand && (btnExpand.contains(e.target) || btnExpand === e.target)) {
                        return;
                    }

                    // Si el clic fue en el modal de confirmación de salida, no colapsar
                    var modalSalida = targetDoc.getElementById('bolimur-exit-confirm-modal');
                    if (modalSalida && (modalSalida.contains(e.target) || modalSalida === e.target)) {
                        return;
                    }

                    // Si la barra lateral está abierta (existe el botón de colapso en el DOM)
                    var btnCollapse = targetDoc.querySelector(
                        '[data-testid="stSidebarCollapseButton"] button, ' +
                        '[data-testid="stSidebarCollapseButton"], ' +
                        'button[aria-label="Collapse sidebar"]'
                    );
                    if (btnCollapse) {
                        // El usuario ha pulsado en la ventana derecha para ir a la aplicación:
                        // Desplazar/ocultar la barra lateral izquierda inmediatamente
                        btnCollapse.click();
                    }
                } catch(err) {
                    console.error('Error auto-colapso sidebar:', err);
                }
            }

            targetDoc.addEventListener('click', onVentanaDerechaClick, false);
            targetWin.__bolimur_sidebar_click_installed = true;
        }

        instalarAutoColapsoSidebar();

    })();
    </script>
    """
    components.html(codigo_html, height=0, width=0)

def procesar_salida_url(auth_manager_mod=None):
    """
    Verifica si se recibió el parámetro '?salir=1' en la URL tras confirmar la salida.
    Si es así, cierra la sesión limpiamente.
    """
    try:
        if st.query_params.get("salir") in ("1", "true", "True"):
            try:
                del st.query_params["salir"]
            except Exception:
                pass
            if auth_manager_mod and hasattr(auth_manager_mod, "cerrar_sesion"):
                auth_manager_mod.cerrar_sesion()
            else:
                st.session_state["usuario_autenticado"] = None
                st.session_state["sesion_cerrada_manual"] = True
                st.rerun()
    except Exception:
        pass

def mostrar_dialogo_confirmacion_salida(auth_manager_mod=None):
    """
    Muestra un diálogo nativo Streamlit para confirmar salida si se pulsa el botón 'Salir'.
    """
    if hasattr(st, "dialog"):
        @st.dialog("⚠️ Confirmar salida de Bolimur")
        def _dialog():
            st.markdown("### ¿Deseas salir de la aplicación?")
            st.write("Se cerrará la sesión actual de trabajo en **Bolimur REBT PRO**.")
            st.caption("Asegúrate de haber guardado tus cálculos o proyectos.")
            c_stay, c_exit = st.columns(2)
            with c_stay:
                if st.button("🛡️ Permanecer aquí", type="primary", use_container_width=True, key="dlg_btn_stay_exit"):
                    st.rerun()
            with c_exit:
                if st.button("🚪 Sí, salir", type="secondary", use_container_width=True, key="dlg_btn_conf_exit"):
                    if auth_manager_mod and hasattr(auth_manager_mod, "cerrar_sesion"):
                        auth_manager_mod.cerrar_sesion()
                    else:
                        st.session_state["usuario_autenticado"] = None
                        st.session_state["sesion_cerrada_manual"] = True
                        st.rerun()
        _dialog()
    else:
        if auth_manager_mod and hasattr(auth_manager_mod, "cerrar_sesion"):
            auth_manager_mod.cerrar_sesion()
        else:
            st.session_state["usuario_autenticado"] = None
            st.session_state["sesion_cerrada_manual"] = True
            st.rerun()

def mostrar_dialogo_cambiar_cuenta(auth_manager_mod=None):
    """
    Muestra un diálogo nativo Streamlit para confirmar el cambio de usuario/cuenta.
    """
    if hasattr(st, "dialog"):
        @st.dialog("🔄 Cambiar de Cuenta")
        def _dialog_cambiar():
            st.markdown("### ¿Deseas cambiar de cuenta?")
            st.write("Se cerrará la sesión actual para permitirte iniciar sesión con otra cuenta de Google o credenciales.")
            c_stay, c_exit = st.columns(2)
            with c_stay:
                if st.button("🛡️ Cancelar", type="primary", use_container_width=True, key="dlg_btn_stay_switch"):
                    st.rerun()
            with c_exit:
                if st.button("🔄 Sí, cambiar", type="secondary", use_container_width=True, key="dlg_btn_conf_switch"):
                    if auth_manager_mod and hasattr(auth_manager_mod, "cerrar_sesion"):
                        auth_manager_mod.cerrar_sesion()
                    else:
                        st.session_state["usuario_autenticado"] = None
                        st.session_state["sesion_cerrada_manual"] = True
                        st.rerun()
        _dialog_cambiar()
    else:
        if auth_manager_mod and hasattr(auth_manager_mod, "cerrar_sesion"):
            auth_manager_mod.cerrar_sesion()
        else:
            st.session_state["usuario_autenticado"] = None
            st.session_state["sesion_cerrada_manual"] = True
            st.rerun()

