function display_menu() {
    
    console.log("Display menu")
    // var menu_template = $("<div class = row></div>");
    var vote_menu = $('<button class="menu_button" id="vote_menu">Vote</button>');
    var blockchain_menu = $('<button class="menu_button" id="blockchain_menu">Blockchain</button>');
    var results_menu = $('<button class="menu_button" id="results_menu">Results</button>');
    var networks_menu = $('<button class="menu_button" id="networks_menu">Networks</button>');
    
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

    $(".menu_header").append(vote_menu);
    $(".menu_header").append(blockchain_menu);
    $(".menu_header").append(results_menu);
    $(".menu_header").append(networks_menu);

}

function display_vote() {
    
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