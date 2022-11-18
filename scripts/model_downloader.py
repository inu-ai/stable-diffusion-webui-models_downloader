import gradio as gr
import modules.ui
from modules.shared import opts, cmd_opts
from modules import shared, scripts
from modules import script_callbacks
from modules import sd_vae, extensions

import os
base_dir = scripts.basedir()

def get_jinja2_template():
    import jinja2
    templates_path = os.path.join(base_dir, "templates")
    fileSystemLoader = jinja2.FileSystemLoader(searchpath=templates_path)
    env = jinja2.Environment(loader=fileSystemLoader)
    template = env.get_template('models.html')
    return template
     
def init_models(models):
    import re
    for model in models:
        model["is_downloaded"] = False
        url = model["url"]

        if url.startswith("https://huggingface.co/"):
            ret = re.match("https://huggingface.co/([^/]+)/([^/]+)/[^/]+/[^/]+/(.+)", url)
            if ret:
                model["repository_url"] = f"https://huggingface.co/{ret.group(1)}/{ret.group(2)}/"
        elif url.startswith("https://github.com/"):
            ret = re.match("https://github.com/([^/]+)/([^/]+)/[^/]+/[^/]+/(.+)", url)
            if ret:
                model["repository_url"] = f"https://github.com/{ret.group(1)}/{ret.group(2)}/"

def load_models_json():
    import json
    modesl_json_path = os.path.join(base_dir, "models.json")
    json_open = open(modesl_json_path, 'r')
    json_load = json.load(json_open)
    init_models(json_load["models"])
    return json_load

available_models = load_models_json()


def filter_models_json(tag):
    models_json = list(filter(lambda x: tag == x["tags"][0], available_models["models"]))
    return {"models" : models_json}

def create_html(tag):
    template = get_jinja2_template()
    models_json = filter_models_json(tag)
    rendered = template.render(models_json)
    return rendered

def resolve_models_url(url):
    if url.startswith("https://github.com/"):
        url = url.replace("/blob/", "/raw/")
    elif url.startswith("https://huggingface.co/"):
        url = url.replace("/blob/", "/resolve/")
    return url

def update_models_json_to_downloaded(url):
    global available_models
    for model in available_models["models"]:
        if url == model["url"]:
            model["is_downloaded"] = True
            break

tags_path = {
    "stable_diffusion": sd_vae.model_path,
    "vae": sd_vae.vae_path,
    "textual_inversion_embedding": shared.cmd_opts.embeddings_dir,
    "hypernetwork": shared.cmd_opts.hypernetwork_dir,
    "aesthetic_embedding": os.path.join(extensions.extensions_dir,"stable-diffusion-webui-aesthetic-gradients","aesthetic_embeddings"),
}

def download_model_button_click(token, url, tag):
    from tqdm import tqdm
    import requests

    file_name = url.split("/")[-1]
    path = tags_path[tag]
    file_path = f"{path}/{file_name}"

    raw_url = resolve_models_url(url)
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get(raw_url, headers=headers, stream=True, allow_redirects=True)
    
    total_size_in_bytes= int(response.headers.get('content-length', 0))
    block_size = 1024 #1 Kibibyte
    progress_bar = tqdm(total=total_size_in_bytes, unit='iB', unit_scale=True)
    with open(file_path, 'wb') as file:
        for data in response.iter_content(block_size):
            progress_bar.update(len(data))
            file.write(data)
    progress_bar.close()
    if os.path.getsize(file_path) == 0:
        os.remove(file_path)
        print("ERROR, enter hugging face token")
    elif total_size_in_bytes != 0 and progress_bar.n != total_size_in_bytes:
        print("ERROR, something went wrong")
    else:
        update_models_json_to_downloaded(url)

    html = create_html(tag)
    return [html]

def create_common_tag(tag):
    html = create_html(tag)

    hugging_face_token_text = gr.Textbox(elem_id="hugging_face_token_text", label="hugging_face_token", visible=True)
    download_model_button = gr.Button(elem_id="download_model_button", visible=False)
    download_url_text = gr.Textbox(elem_id="download_url_text", visible=False)
    download_tag_text = gr.Textbox(value=tag, elem_id="download_tag_text", visible=False)
    download_html = gr.HTML(html)

    download_model_button.click(
        fn=download_model_button_click,
        inputs=[hugging_face_token_text, download_url_text, download_tag_text],
        outputs=[download_html],
    )

def create_stable_diffusions_tag(tag):
    create_common_tag(tag)

def create_vaes_tag(tag):
    create_common_tag(tag)

def create_textual_inversion_embeddings_tag(tag):
    create_common_tag(tag)

def create_hypernetworks_tag(tag):
    create_common_tag(tag)

def create_aesthetic_embeddings_tag(tag):
    create_common_tag(tag)

tags_func = {
    "stable_diffusion": create_stable_diffusions_tag,
    "vae": create_vaes_tag,
    "textual_inversion_embedding": create_textual_inversion_embeddings_tag,
    "hypernetwork": create_hypernetworks_tag,
    "aesthetic_embedding": create_aesthetic_embeddings_tag,
}

def check_aesthetic_gradients():        
    result = False
    for ext in extensions.extensions:
        if "aesthetic-gradients" in ext.name:
            result = True
            break
    return result 

def on_ui_tabs():
    with gr.Blocks(analytics_enabled=False) as models_downloader:
        with gr.Tabs(elem_id="models_downloader_tab") as tabs:
            for tag, func in tags_func.items():
                if "aesthetic_embedding"== tag and not check_aesthetic_gradients():
                    continue
                with gr.TabItem(tag):
                    func(tag)
    return [(models_downloader, "Downloader", "models_downloader")]


script_callbacks.on_ui_tabs(on_ui_tabs)
