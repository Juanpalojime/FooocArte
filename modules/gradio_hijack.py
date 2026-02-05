# gradio_hijack.py
"""
Gradio Hijack Maestro para Fooocus
----------------------------------
Permite interceptar todos los componentes de Gradio y manipularlos dinámicamente
desde código externo usando nombres amigables.
Compatible con sliders, checkboxes, buttons, tabs, images, dropdowns, etc.
"""

global_components = {}

# =====================================
# Nombres amigables para Fooocus
# =====================================
friendly_names = {
    # Tabs y checkboxes
    "Advanced": "advanced_checkbox",
    "Developer Debug Mode": "dev_mode",
    "Debug Tools": "dev_tools_tab",
    "Control": "control_tab",
    "Canny": "canny_tab",
    "Inpaint": "inpaint_tab",
    "FreeU": "freeu_tab",

    # Sliders
    "Guidance Scale": "guidance_scale",
    "Image Sharpness": "sharpness",
    "Positive ADM Guidance Scaler": "adm_scaler_positive",
    "Negative ADM Guidance Scaler": "adm_scaler_negative",
    "ADM Guidance End At Step": "adm_scaler_end",
    "CFG Mimicking from TSNR": "adaptive_cfg",
    "CLIP Skip": "clip_skip",
    "Softness of ControlNet": "controlnet_softness",
    "Canny Low Threshold": "canny_low_threshold",
    "Canny High Threshold": "canny_high_threshold",
    "Inpaint Denoising Strength": "inpaint_strength",
    "Inpaint Respective Field": "inpaint_respective_field",
    "Mask Erode or Dilate": "inpaint_erode_or_dilate",
    "GroundingDINO Box Erode or Dilate": "dino_erode_or_dilate",
    "B1": "freeu_b1",
    "B2": "freeu_b2",
    "S1": "freeu_s1",
    "S2": "freeu_s2",
    "Forced Overwrite of Sampling Step": "overwrite_step",
    "Forced Overwrite of Refiner Switch Step": "overwrite_switch",
    "Forced Overwrite of Generating Width": "overwrite_width",
    "Forced Overwrite of Generating Height": "overwrite_height",
    "Forced Overwrite of Denoising Strength of \"Vary\"": "overwrite_vary_strength",
    "Forced Overwrite of Denoising Strength of \"Upscale\"": "overwrite_upscale_strength",

    # Dropdowns
    "Refiner swap method": "refiner_swap_method",
    "Sampler": "sampler_name",
    "Scheduler": "scheduler_name",
    "VAE": "vae_name",
    "Inpaint Engine": "inpaint_engine",

    # Buttons
    "Generate": "generate_button",
    "Reset": "reset_button",
    "Refresh": "refresh_files",
    "Load Parameters": "load_parameter_button",
    "Metadata Import": "metadata_import_button",
    "Generate Mask": "generate_mask_button",
    "Describe": "describe_btn",

    # Checkboxes
    "Disable Preview": "disable_preview",
    "Disable Intermediate Results": "disable_intermediate_results",
    "Disable seed increment": "disable_seed_increment",
    "Black Out NSFW": "black_out_nsfw",
    "Save only final enhanced image": "save_final_enhanced_image_only",
    "Save Metadata to Images": "save_metadata_to_images",
    "Read wildcards in order": "read_wildcards_in_order",
    "Debug Preprocessors": "debugging_cn_preprocessor",
    "Skip Preprocessors": "skipping_cn_preprocessor",
    "Mixing Image Prompt and Vary/Upscale": "mixing_image_prompt_and_vary_upscale",
    "Mixing Image Prompt and Inpaint": "mixing_image_prompt_and_inpaint",
    "Debug Inpaint Preprocessing": "debugging_inpaint_preprocessor",
    "Debug Enhance Masks": "debugging_enhance_masks_checkbox",
    "Debug GroundingDINO": "debugging_dino",
    "Disable initial latent in inpaint": "inpaint_disable_initial_latent",
    "Enabled": "freeu_enabled",
}

# =====================================
# Registro y manipulación de componentes
# =====================================
def register_component(name, component):
    """Registrar un componente con un nombre único."""
    global_components[name] = component

def set_value(name, value):
    comp = global_components.get(name)
    if comp:
        return comp.update(value=value)
    return None

def set_visible(name, visible=True):
    comp = global_components.get(name)
    if comp:
        return comp.update(visible=visible)
    return None

def set_interactive(name, interactive=True):
    comp = global_components.get(name)
    if comp:
        return comp.update(interactive=interactive)
    return None

def update_multiple(updates: dict):
    """
    Actualizar múltiples componentes al mismo tiempo.
    Example:
        {
            "Guidance Scale": 12.5,
            "Advanced": True,
            "Developer Debug Mode": {"visible": True, "interactive": False},
        }
    """
    results = []
    for key, value in updates.items():
        name = friendly_names.get(key, key)
        if isinstance(value, dict):
            if 'value' in value:
                results.append(set_value(name, value['value']))
            if 'visible' in value:
                results.append(set_visible(name, value['visible']))
            if 'interactive' in value:
                results.append(set_interactive(name, value['interactive']))
        else:
            results.append(set_value(name, value))
    return results

def list_components():
    """Listar todos los componentes registrados."""
    return list(global_components.keys())

def hijack_all(gradio_root):
    """
    Recorrer todos los componentes de Gradio y registrarlos automáticamente.
    Compatible con Tabs, Rows, Columns, Sliders, Checkboxes, Buttons, Images, Textboxes, etc.
    """
    def recursive_register(components):
        for comp in components:
            # Registrar hijos si es contenedor
            sub_comps = getattr(comp, 'children', None)
            if sub_comps:
                recursive_register(sub_comps)

            # Obtener nombre real
            name = getattr(comp, 'elem_id', None) or getattr(comp, 'label', None)
            if name:
                # Reemplazar por friendly name si existe
                for friendly, real_name in friendly_names.items():
                    if name == friendly:
                        name = real_name
                        break
                register_component(name, comp)

    recursive_register(gradio_root.components)

# =====================================
# Uso típico:
# =====================================
# import gradio_hijack as crf
# crf.hijack_all(shared.gradio_root)
# crf.set_value("Guidance Scale", 12.5)
# crf.set_visible("Advanced", True)
# crf.update_multiple({
#     "Guidance Scale": 14.0,
#     "Developer Debug Mode": {"visible": False, "interactive": True}
# })
# print(crf.list_components())
