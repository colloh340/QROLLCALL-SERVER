$(document).ready(function(){
    var btn_login = $("#btn-login")
    btn_login.click((event)=>{
        event.preventDefault()
        $('#modal-loading').modal('show');
        var email = $("#input-login-email").val()
        var password = $("#input-login-password").val()
        var remember_me = $("#input-remember-me").val()
        var csrfmiddlewaretoken = $("input[name='csrfmiddlewaretoken']").val()

        if(email.length != 0 && password.length != 0){
            var formData = new FormData()
            formData.append("email", email)
            formData.append("password",password)
            formData.append("remember_me", remember_me)
            formData.append("csrfmiddlewaretoken", csrfmiddlewaretoken)

            fetch("/auth/login/web",{
                method: "POST",
                body:  formData,
                headers:{
                    "Authorization": "bearer none",
                    "Client":"qrollcall.com"
                }
            }).then((response)=>{
                return response.json()
            }).then((data)=>{
                var status = data.status;
                var message = data.message;
                createToast(message, status);
                if(status == 200){
                    window.location.href = "/dashboard";
                }
                
            }).catch((error)=>{
                createToast("Something went wrong "+error, 500);
            }).finally(()=>{
                $('#modal-loading').modal('hide');
            });
        }
    })
    
})