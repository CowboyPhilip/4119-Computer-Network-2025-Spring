function display_menu() {
    
    console.log("Display menu")
    var menu_template = $("<div class = row></div>");
    var vote_menu = $("<button id=vote_menu>Vote</button>");
    var blockchain_menu = $("<button id=blockchain_menu>Blockchain</button>");
    var results_menu = $("<button id=results_menu>Results</button>");
    var networks_menu = $("<button id=networks_menu>Networks</button>");
    
    $(vote_menu).click(function() {
        switch_page("/vote");
    });
    $(blockchain_menu).click(function() {
        switch_page("/blockchain");
    });
    $(results_menu).click(function() {
        switch_page("/results");
    });
    $(networks_menu).click(function() {
        switch_page("/network");
    });

    menu_template.append(vote_menu);
    menu_template.append(blockchain_menu);
    menu_template.append(results_menu);
    menu_template.append(networks_menu);
    $(".menu_headers").append(menu_template);

}

function switch_page(page) {
    console.log("Switch page")
    $.ajax({
        type: "GET",
        url: page,
        success: function(response) {
            // console.log(response)
            $(".main").html(response);
        },
        error: function(request, status, error) {
            console.log("Error");
            console.log(request)
            console.log(status)
            console.log(error)
        }
    });
}

$(document).ready(function() {
    console.log("Ready")
    display_menu();
})