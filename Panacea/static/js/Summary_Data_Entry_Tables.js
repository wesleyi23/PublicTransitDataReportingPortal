$(document).ready(function() {
    $('.this-year').children("input").attr("disabled", false);
    $('.two-years-ago').children("input").attr("disabled", true);
    $('.previous-year').children("input").attr("disabled", true);

    $('.this-year').css("display", "")
    $('.two-years-ago.comments').css("display", "none");
    $('.previous-year.comments').css("display", "none");

    $('.this-year').children(".edit-column").css("display", "none");
});

$('.disabled-form').submit(function(){
    $(".disabled-form :disabled").removeAttr('disabled');
});

$('.edit-column').click(function(){
    console.log('click');

    switch($(this).parent().prop("class")){
        case 'this-year':
            $('.this-year').children("input").attr("disabled", false);
            $('.two-years-ago').children("input").attr("disabled", true);
            $('.previous-year').children("input").attr("disabled", true);

            $('.this-year.comments').show(25);
            $('.two-years-ago.comments').hide(25);
            $('.previous-year.comments').hide(25);

            $('.this-year').children(".edit-column").css("display", "none");
            $('.two-years-ago').children(".edit-column").css("display", "");
            $('.previous-year').children(".edit-column").css("display", "");
            break;
        case 'previous-year':
            $('.this-year').children("input").attr("disabled", true);
            $('.two-years-ago').children("input").attr("disabled", true);
            $('.previous-year').children("input").attr("disabled", false);

            $('.previous-year.comments').show(25);
            $('.this-year.comments').hide(25);
            $('.two-years-ago.comments').hide(25);

            $('.this-year').children(".edit-column").css("display", "");
            $('.two-years-ago').children(".edit-column").css("display", "");
            $('.previous-year').children(".edit-column").css("display", "none");
            break;
        case 'two-years-ago':
            $('.this-year').children("input").attr("disabled", true);
            $('.two-years-ago').children("input").attr("disabled", false);
            $('.previous-year').children("input").attr("disabled", true);

            $('.two-years-ago.comments').show(25);
            $('.this-year.comments').hide(25);
            $('.previous-year.comments').hide(25);

            $('.this-year').children(".edit-column").css("display", "");
            $('.two-years-ago').children(".edit-column").css("display", "none");
            $('.previous-year').children(".edit-column").css("display", "");
            break;
    }
})