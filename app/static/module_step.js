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

const next = async (module_name, step) => {
    try {
        const response = await fetch(`/modules/${module_name}/step/${step}/next`, {
            method: "POST",
            credentials: "include"
        })
        const result = await response.json();

        if ("url" in result) {
            window.location.href = result.url;
            return
        }

        checkStatus.value = "Not Implemented"
        checkToast.value = result.toast
    }
    catch (error) {
        checkStatus.value = "ERROR"
        checkToast.value = "An error occured: " + error.message
    }
}
