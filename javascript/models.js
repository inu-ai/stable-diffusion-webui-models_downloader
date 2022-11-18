function start_download_model(button, url, tag){
    button.disabled = "disabled"
    button.value = "Downloading..."

    let textarea = gradioApp().querySelector(`#download_url_text_${tag} textarea`)
    textarea.value = url
    textarea.dispatchEvent(new Event("input", { bubbles: true }))
    
    textarea = gradioApp().querySelector(`#download_tag_text_${tag} textarea`)
    textarea.value = tag
    textarea.dispatchEvent(new Event("input", { bubbles: true }))

    gradioApp().querySelector(`#download_model_button_${tag}`).click()
}
