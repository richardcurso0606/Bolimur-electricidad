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
    4. Interceptar el botón Atrás y gestos de retroceso en móviles/tablets (popstate).
    5. Auto-colapsar la barra lateral izquierda al pulsar en el contenido de la derecha.
    """
    codigo_html = """
    <script>
    (function() {
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

        // Si ya está inyectado el script persistente en el documento principal, no duplicar
        if (targetDoc.getElementById('bolimur-guard-core-script')) {
            return;
        }

        var scriptElem = targetDoc.createElement('script');
        scriptElem.id = 'bolimur-guard-core-script';
        scriptElem.textContent = `
        (function() {
            var win = window;
            var doc = document;

            // 1. Protección contra cierre accidental de pestaña/ventana (beforeunload)
            if (!win.__bolimur_beforeunload_active) {
                win.__bolimur_allow_exit = false;
                win.addEventListener('beforeunload', function(e) {
                    if (win.__bolimur_allow_exit) {
                        return undefined;
                    }
                    var mensaje = '¿Estás seguro de que deseas salir de Bolimur REBT? Es posible que los datos no guardados se pierdan.';
                    e.preventDefault();
                    e.returnValue = mensaje;
                    return mensaje;
                });
                win.__bolimur_beforeunload_active = true;
            }

            // 2. Crear el Modal de Confirmación en el Documento Principal si no existe
            var modalId = 'bolimur-exit-confirm-modal';
            var modal = doc.getElementById(modalId);

            if (!modal) {
                modal = doc.createElement('div');
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

                modal.innerHTML = '<div id="bolimur-modal-box" style="' + [
                    'background: #ffffff !important',
                    'border: 2px solid #0284c7 !important',
                    'border-radius: 16px !important',
                    'box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5) !important',
                    'width: 90% !important',
                    'max-width: 490px !important',
                    'padding: 26px 24px !important',
                    'text-align: center !important',
                    'box-sizing: border-box !important',
                    'transform: scale(0.92) !important',
                    'transition: transform 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important'
                ].join(';') + '">' +
                    '<div style="width: 58px !important; height: 58px !important; background: #fffbeb !important; border: 2px solid #fde68a !important; border-radius: 50% !important; display: flex !important; align-items: center !important; justify-content: center !important; margin: 0 auto 16px auto !important; font-size: 28px !important;">⚠️</div>' +
                    '<div style="font-size: 11px !important; font-weight: 700 !important; color: #0284c7 !important; text-transform: uppercase !important; letter-spacing: 0.05em !important; margin-bottom: 6px !important;">⚡ Bolimur REBT PRO • Control de Salida</div>' +
                    '<h3 style="margin: 0 0 10px 0 !important; color: #0f172a !important; font-size: 20px !important; font-weight: 700 !important;">¿Deseas salir de la aplicación?</h3>' +
                    '<p style="margin: 0 0 22px 0 !important; color: #475569 !important; font-size: 14px !important; line-height: 1.55 !important;">Has pulsado <strong>Escape</strong> o el botón <strong>Atrás</strong>.<br>Para evitar pérdida de cálculos técnicos, debes <strong>confirmar</strong> si realmente deseas salir.</p>' +
                    '<div style="display: flex !important; gap: 12px !important; justify-content: center !important;">' +
                        '<button id="bolimur-btn-permanecer" type="button" style="flex: 1.2 !important; background: #0284c7 !important; color: #ffffff !important; border: none !important; padding: 12px 16px !important; border-radius: 10px !important; font-size: 14px !important; font-weight: 600 !important; cursor: pointer !important; box-shadow: 0 4px 10px rgba(2, 132, 199, 0.3) !important;">🛡️ Permanecer aquí</button>' +
                        '<button id="bolimur-btn-salir" type="button" style="flex: 0.9 !important; background: #fef2f2 !important; color: #dc2626 !important; border: 1.5px solid #f87171 !important; padding: 12px 14px !important; border-radius: 10px !important; font-size: 14px !important; font-weight: 600 !important; cursor: pointer !important;">🚪 Sí, salir</button>' +
                    '</div>' +
                    '<div style="margin-top: 14px !important; font-size: 12px !important; color: #94a3b8 !important;">Si pulsas <em>Permanecer</em> o haces clic fuera, seguirás dentro sin perder nada.</div>' +
                '</div>';

                doc.body.appendChild(modal);

                function abrirModal() {
                    modal.style.display = 'flex';
                    setTimeout(function() {
                        modal.style.opacity = '1';
                        var card = doc.getElementById('bolimur-modal-box');
                        if (card) card.style.transform = 'scale(1)';
                        var btnStay = doc.getElementById('bolimur-btn-permanecer');
                        if (btnStay) btnStay.focus();
                    }, 10);
                    win.__bolimur_modal_visible = true;
                }

                function cerrarModal() {
                    modal.style.opacity = '0';
                    var card = doc.getElementById('bolimur-modal-box');
                    if (card) card.style.transform = 'scale(0.92)';
                    setTimeout(function() {
                        modal.style.display = 'none';
                    }, 200);
                    win.__bolimur_modal_visible = false;
                }

                win.__bolimur_abrir_modal = abrirModal;
                win.__bolimur_cerrar_modal = cerrarModal;

                var btnStay = doc.getElementById('bolimur-btn-permanecer');
                if (btnStay) {
                    btnStay.addEventListener('click', function(ev) {
                        ev.preventDefault();
                        ev.stopPropagation();
                        cerrarModal();
                    });
                }

                var btnExit = doc.getElementById('bolimur-btn-salir');
                if (btnExit) {
                    btnExit.addEventListener('click', function(ev) {
                        ev.preventDefault();
                        ev.stopPropagation();
                        win.__bolimur_allow_exit = true;
                        cerrarModal();
                        try {
                            win.close();
                        } catch (err) {}
                        setTimeout(function() {
                            var baseUrl = win.location.pathname || '/';
                            win.location.href = baseUrl + '?salir=1';
                        }, 200);
                    });
                }

                modal.addEventListener('click', function(ev) {
                    if (ev.target === modal) {
                        cerrarModal();
                    }
                });
            }

            // 3. Interceptor universal de la tecla Escape (Desktop / Tablet)
            function onKeyDownEscape(e) {
                var esEscape = (e.key === 'Escape' || e.key === 'Esc' || e.keyCode === 27 || e.code === 'Escape');
                if (esEscape) {
                    if (win.__bolimur_modal_visible) {
                        e.preventDefault();
                        e.stopPropagation();
                        e.stopImmediatePropagation();
                        if (typeof win.__bolimur_cerrar_modal === 'function') {
                            win.__bolimur_cerrar_modal();
                        }
                        return false;
                    }

                    try {
                        var openDropdown = doc.querySelector('div[data-baseweb="popover"], div[role="listbox"], ul[role="listbox"]');
                        if (openDropdown && openDropdown.offsetParent !== null) {
                            return;
                        }
                    } catch(err) {}

                    e.preventDefault();
                    e.stopPropagation();
                    e.stopImmediatePropagation();

                    if (typeof win.__bolimur_abrir_modal === 'function') {
                        win.__bolimur_abrir_modal();
                    }
                    return false;
                }
            }

            if (!win.__bolimur_esc_installed) {
                win.addEventListener('keydown', onKeyDownEscape, true);
                win.addEventListener('keyup', function(e) {
                    if (e.key === 'Escape' || e.keyCode === 27) {
                        e.preventDefault();
                        e.stopPropagation();
                        e.stopImmediatePropagation();
                    }
                }, true);
                doc.addEventListener('keydown', onKeyDownEscape, true);
                win.__bolimur_esc_installed = true;
            }

            // 4. Interceptor permanente para móvil: Botón Atrás y Deslizar Atrás (popstate)
            function armarHistorial() {
                try {
                    if (!win.history.state || !win.history.state.bolimur) {
                        win.history.pushState({ bolimur: 'active', t: Date.now() }, '', win.location.href);
                    }
                } catch(e) {}
            }

            if (!win.__bolimur_popstate_installed) {
                // Cebar estado inicial en el historial
                armarHistorial();

                // Re-armar el historial con cualquier interacción táctil o clic (en ventana derecha o menú izquierdo)
                doc.addEventListener('touchstart', armarHistorial, { capture: true, passive: true });
                doc.addEventListener('touchend', armarHistorial, { capture: true, passive: true });
                doc.addEventListener('pointerdown', armarHistorial, { capture: true, passive: true });
                doc.addEventListener('click', armarHistorial, { capture: true, passive: true });
                win.addEventListener('focus', armarHistorial, { passive: true });
                win.addEventListener('pageshow', armarHistorial, { passive: true });

                // Mantener el estado en historial de forma continua para blindar el menú vertical izquierdo
                setInterval(function() {
                    armarHistorial();
                }, 600);

                win.addEventListener('popstate', function(ev) {
                    if (win.__bolimur_allow_exit) {
                        return;
                    }

                    // Re-empujar inmediatamente para bloquear la salida involuntaria
                    try {
                        win.history.pushState({ bolimur: 'active', t: Date.now() }, '', win.location.href);
                    } catch(e) {}

                    // Si el modal ya estaba visible, cerrarlo (cancelar salida)
                    if (win.__bolimur_modal_visible) {
                        if (typeof win.__bolimur_cerrar_modal === 'function') {
                            win.__bolimur_cerrar_modal();
                        }
                        return;
                    }

                    // Si el menú lateral está abierto en móvil, cerrarlo para despejar la vista
                    try {
                        var sidebar = doc.querySelector('[data-testid="stSidebar"]');
                        var btnCollapse = doc.querySelector(
                            '[data-testid="stSidebarCollapseButton"] button, ' +
                            '[data-testid="stSidebarCollapseButton"], ' +
                            'button[aria-label="Collapse sidebar"]'
                        );
                        if (sidebar && btnCollapse && win.innerWidth < 992) {
                            btnCollapse.click();
                        }
                    } catch(err) {}

                    // ¡MOSTRAR SIEMPRE EL MODAL DE CONFIRMACIÓN!
                    // Protege por igual tanto la ventana derecha como el menú vertical izquierdo
                    if (typeof win.__bolimur_abrir_modal === 'function') {
                        win.__bolimur_abrir_modal();
                    }
                }, true);

                win.__bolimur_popstate_installed = true;
            }

            // 5. Desplazar/colapsar la barra lateral izquierda al pulsar en la ventana derecha
            if (!win.__bolimur_sidebar_autocollapse) {
                doc.addEventListener('click', function(e) {
                    try {
                        var sidebar = doc.querySelector('[data-testid="stSidebar"]');
                        if (!sidebar) return;
                        if (sidebar.contains(e.target)) return;

                        var btnExpand = doc.querySelector('[data-testid="stExpandSidebarButton"]');
                        if (btnExpand && (btnExpand.contains(e.target) || btnExpand === e.target)) return;

                        var mBox = doc.getElementById('bolimur-exit-confirm-modal');
                        if (mBox && (mBox.contains(e.target) || mBox === e.target)) return;

                        var btnCollapse = doc.querySelector(
                            '[data-testid="stSidebarCollapseButton"] button, ' +
                            '[data-testid="stSidebarCollapseButton"], ' +
                            'button[aria-label="Collapse sidebar"]'
                        );
                        if (btnCollapse) {
                            btnCollapse.click();
                        }
                    } catch(err) {}
                }, false);
                win.__bolimur_sidebar_autocollapse = true;
            }
        })();
        `;
        (targetDoc.head || targetDoc.body).appendChild(scriptElem);
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

