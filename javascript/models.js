function start_download_model(button, url, tag){
    button.disabled = "disabled"
    button.value = "Downloading..."

    let textarea = gradioApp().querySelector('#download_url_text textarea')
    textarea.value = url
    textarea.dispatchEvent(new Event("input", { bubbles: true }))
    
    textarea = gradioApp().querySelector('#download_tag_text textarea')
    textarea.value = tag
    textarea.dispatchEvent(new Event("input", { bubbles: true }))

    gradioApp().querySelector('#download_model_button').click()
}
