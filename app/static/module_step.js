const checkStatus = document.getElementById("check_status")
const checkToast = document.getElementById("check_toast")
const checkButton = document.getElementById("check_button")

const check = async () => {
    try {
        const response = await fetch("", {
            method: "POST",
            credentials: "include"
        })
        const result = await response.json()
        checkStatus.value = result.status
        checkToast.value = result.message
    }
    catch (error) {
        checkStatus.value = "ERROR"
        checkToast.value = "An error occured: " + error.message
    }
}
