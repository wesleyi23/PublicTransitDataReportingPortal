$(document).ready(function() {
    $(".post-form").submit(function(event) {
        event.preventDefault();
        var FormName = $(this).attr('name');
        var errField = $(this).attr('data-errField')
        $.ajax({ data: $(this).serialize(),
            dataType: 'json',
            type: $(this).attr('method'),
            url: $(this).attr('action'),
            success: function(response) {
                console.log(response);
                if(response['success']) {
                    // $("#feedbackmessage").html("<div class='alert alert-success'>Successfully edited user information, thank you!</div>");
                    // $("#post-form").addClass("hidden");
                    $("#carouselIndicators").carousel("next");
                } else if(response['error']) {
                    console.log("#" + FormName + errField + "_err");

                    $("#" + FormName + "_err").html("<div class='alert alert-danger'>" +
                        response['error'][errField] +"</div>");
                } else if(response['redirect']) {
                    window.location = response['redirect'];
                }
            },
            error: function (request, status, error) {
                console.log(request.responseText);
            }
        });
    });
});


$(document).ready(function($) {
    $(".clickable-row").click(function() {
        window.location = $(this).data("href");
    });
});


