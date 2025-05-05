var pageCache = {}

function display_menu() {
    
    $("#vote_menu").click(function() {
        switch_page("/vote");
    });
    $("#blockchain_menu").click(function() {
        switch_page("/blockchain");
    });
    $("#results_menu").click(function() {
        switch_page("/results");
    });
    $("#network_menu").click(function() {
        switch_page("/network");
    });

}

function vote_interaction() {
    
    $("#cast_vote").click(function() {
        $(".error_box").empty();
        var candidateData = {"candidate": $("#candidate_selector").text()};
        $.ajax({
            type: "POST",
            url: "/vote/cast_vote",
            contentType: "application/json; charset=utf-8",
            data: JSON.stringify(candidateData),
            dataType: "json",
            success: function(response) {
                if (response.transaction_log) {
                    $("#transaction_box").append(response.transaction_log);
                    delete pageCache["/blockchain"];
                } else {
                    display_info("Error", response.error);
                }
                pageCache["/vote"] = $("#main").html();
            }
        });
    });

    $("#mine_block").click(function() {
        $(".error_box").empty();
        $.ajax({
            type: "POST",
            url: "/vote/mine_block",
            dataType: "json",
            success: function(response) {
                if (response.transaction_log) {
                    $("#transaction_box").append(response.transaction_log);
                    delete pageCache["/blockchain"];
                } else if (response.error) {
                    display_info("Error", response.error);
                } else {
                    display_info("Info", response.info);
                }
                pageCache["/vote"] = $("#main").html();
            }
        });
    });

    $("#auto_mine").change(function() {
        var autoMineData = {"auto_mine": $('#auto_mine').prop('checked')};
        $.ajax({
            type: "POST",
            url: "/vote/auto_mine",
            contentType: "application/json; charset=utf-8",
            data: JSON.stringify(autoMineData),
            dataType: "json",
            success: function(response) {
                if ($('#auto_mine').prop('checked'))
                    $('#auto_mine').attr("checked", "checked");
                else
                    $('#auto_mine').removeAttr("checked");
                pageCache["/vote"] = $("#main").html();
            }
        });
    });

}

// display func should take html and all jsons as parameters to display at same time
function load_blockchain(html) {

    infoDict = {}
    blockTableDict = {}
    
    $.ajax({
        type: "GET",
        url: "/blockchain/info",
        dataType: "json",
        success: function(response) {
            infoDict = response;
            $.ajax({
                type: "GET",
                url: "/blockchain/display",
                dataType: "json",
                success: function(response) {
                    blockTableDict = response;
                    display_blockchain(html, infoDict, blockTableDict);
                }
            });
        }
    });

}

function display_blockchain(html, infoDict, blockTableDict) {
    
    console.log(blockTableDict);
    
    var i_icon = ('<input class="icon" type="image" ' + 
        'src="../static/images/red_info_icon.png" value=');
    
    $("#main").html(html);
    main_alignment();

    $("#chain_length").text(infoDict.chain_length);
    $("#last_block").text(infoDict.last_block_hash);
    $("#pending_transactions").text(infoDict.pending_transactions);
    $("#mining").text(infoDict.mining);

    for (let i = 0; i < Object.keys(blockTableDict).length; i++) {
        var newRow = `
            <tr>
                <td>` + i + `</td>
                <td>` + blockTableDict[i].hash + `</td>
                <td>` + blockTableDict[i].prev_hash + `</td>
                <td>` + blockTableDict[i].nonce + `</td>
                <td>` + blockTableDict[i].merkle_root + `</td>
                <td>` + blockTableDict[i].time + `</td>
                <td>` + blockTableDict[i].transactions + " " + i_icon + i + ` ></td>
            </tr>
        `;
        $("#blockchain_tbody").append(newRow);
    }

    pageCache["/blockchain"] = $("#main").html();
    blockchain_interaction();

}

function blockchain_interaction() {

    $(".icon").on('click', function(event) {
        event.preventDefault();
        $("#block_no").text($(this).val());
        $.ajax({
            type: "GET",
            url: "/blockchain/transactions",
            contentType: "charset=utf-8",
            data: "block=" + $(this).val(),
            dataType: "json",
            success: function(response) {
                $("#transactions_tbody").empty();
                for (let i = 0; i < Object.keys(response).length; i++) {
                    var newRow = `
                        <tr id="this_transaction">
                            <td>` + response[i].transaction_id + `</td>
                            <td>` + response[i].voter_id + `</td>
                            <td>` + response[i].vote_data + `</td>
                            <td>` + response[i].time + `</td>
                        </tr>
                    `;
                    $("#transactions_tbody").append(newRow);
                }
                pageCache["/blockchain"] = $("#main").html();
            }
        });
    });

}

function results_interaction() {
    $("#vote_img").css("height", 9/16 * $("#vote_img").width());
    pageCache["/results"] = $("#main").html();
}

function display_info(info, error) {
    $(".error_box").append('<span style="font-family: Arial Black, Helvetica, sans-serif;">' + info + ': </span>');
    $(".error_box").append(error);
}

function display_interaction(page) {
    if (page == "/vote") {
        vote_interaction();
    } else
        results_interaction();
}

function load_page_interaction(page, html, cached) {
    if (page == "/vote") {
        $("#main").html(html);
        main_alignment();
        vote_interaction();
    } else if (page == "/blockchain") {
        if (cached) {
            $("#main").html(html);
            main_alignment();
            blockchain_interaction();
        } else {
            load_blockchain(html);
        }
    } else if (page == "/results") {
        $("#main").html(html);
        main_alignment();
        results_interaction();
    } else {
        $("#main").html(html);
        main_alignment();
    }
}

function main_alignment() {
    $("#main").css("margin-left", $("#vote_menu").offset().left);
    $("#error_box").css("margin-left", $("#vote_menu").offset().left);
    $(".box_border").css("width", $("#network_menu").offset().left + 
        $("#network_menu").width() - $("#vote_menu").offset().left - 15);
}

function switch_page(page) {
    $(".error_box").empty();
    if (pageCache[page]) {
        load_page_interaction(page, pageCache[page], true)
        return;
    }
    $.ajax({
        type: "GET",
        url: page,
        success: function(html) {
            load_page_interaction(page, html, false);
        }
    });
}

$(document).ready(function() {
    display_menu();
})