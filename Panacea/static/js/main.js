
// AJAX submit so that the questions can be asked slide rather than redraw page
// used on profilesetup.html
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


// Used on Vanpool_report.html
$(document).ready(function($) {
    $(".clickable-row").click(function() {
        window.location = $(this).data("href");
    });
});


// Used on UserProfile.html and OrganizationProfile.html
$(document).ready(function ($) {
    $(".edit_profile_field").click(function () {
        var field_name = "#id_"+ $(this).data("field_name");
        $(field_name).prop("readonly", false);
        $(field_name).prop("disabled", false);
        $(field_name).css("pointer-events", '');
        $(field_name).attr("class", "form-control")
    })
})

$(document).ready(function ($) {
    $(".AJAX_instant_submit").change( function(e) {
        e.stopImmediatePropagation();
        var FormName = $(this).data('form-name');
        console.log(FormName);
        console.log($("#" + FormName).attr('method'));
        console.log($("#" + FormName).attr('action'));
        var errField = $("#" + FormName).data('err-field');
        $.ajax({ data: $("#" + FormName).serialize(),
            dataType: 'json',
            type: $("#" + FormName).attr('method'),
            url: $("#" + FormName).attr('action'),
            success: function(response) {
                console.log(response);
                if(response['success']) {

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
})



// $(document).ready(function ($) {
//     $(".my_chart_control").change( function(e) {
//         e.stopImmediatePropagation();
//         var FormName = $(this).data('form-name');
//         var errField = $("#" + FormName).data('err-field')
//         $.ajax({ data: $("#" + FormName).serialize(),
//             dataType: 'json',
//             type: $("#" + FormName).attr('method'),
//             url: $("#" + FormName).attr('action'),
//             success: function(response) {
//                 console.log(response);
//                 if(response['success']) {
//                     alert(response['chart_title'][1])
//                     chart.options.title.text = response['chart_title'];
//                     chart.update()
//
//                 } else if(response['error']) {
//                     console.log("#" + FormName + errField + "_err");
//                     $("#" + FormName + "_err").html("<div class='alert alert-danger'>" +
//                         response['error'][errField] +"</div>");
//                 } else if(response['redirect']) {
//                     window.location = response['redirect'];
//                 }
//             },
//             error: function (request, status, error) {
//                 console.log(request.responseText);
//             }
//         });
//     });
// })
