function findTotal(this_year_other_total, previous_year_other_total, two_years_ago_other_total){
    var years = ['this-year', 'previous-year', 'two-years-ago'];
    var year;
    var dict_other_revenue ={
        'this-year': this_year_other_total,
        'previous-year': previous_year_other_total,
        'two-years-ago': two_years_ago_other_total,
    }
    for (year of years){
        var arr = document.querySelectorAll('.'.concat(year).concat(' input.grand-total-sum'));
        var total=0;
        for(var i=0;i<arr.length;i++){
            var my_int = parseInt(arr[i].value.replace(/[^\d.-]/g, ''));
            if(my_int) {
                total += my_int;
            }
        }
        console.log(total);
        grand_total = total + dict_other_revenue[year]
        var grand_total_name = 'grand-total-'.concat(year);
        var sub_total_name = 'sub-total-'.concat(year);
        document.getElementById(grand_total_name).innerHTML = '$'.concat(grand_total.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ","));
        document.getElementById(sub_total_name).innerHTML = '$'.concat(total.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ","));
    }
}