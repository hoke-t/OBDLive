$(document).ready(function () {

    var socket = new WebSocket(window.location.href.replace('http://', 'ws://').replace('http://', 'ws://'));

    function poll () {
        socket.send(JSON.stringify({
            "dtcs": "all"
        }));
    };

    socket.onopen = function open() {
        console.log('WebSockets connection created.');
    };

    if ($('#dtc-body').children().length == 0) {
        $('img').attr('src', '/static/obd/MIL Off.png');
    } else {
        $('img').attr('src', '/static/obd/MIL On.png');
    }

    socket.onmessage = function message(event) {
        dtcs = JSON.parse(event.data)['dtcs'];
        descs = JSON.parse(event.data)['descs'];
        links = JSON.parse(event.data)['links'];
        console.log(dtcs);
        console.log(descs);

        $('#dtc-body').find('tr').remove();

        for (var i = 0; i < dtcs.length; i++) {
            $('#dtc-body').append('<tr><td>' + dtcs[i] + '</td><td>' + descs[i] + '</td><td><a target="_blank" href=http://www.' + links[i] + '>' + links[i] + '</a></td></tr>');
        }

        if ($('#dtc-body').children().length == 0) {
            $('img').attr('src', '/static/obd/MIL Off.png');
        } else {
            $('img').attr('src', '/static/obd/MIL On.png');
        }
    };

    if (socket.readyState == WebSocket.OPEN) {
        socket.onopen();
    }

    window.setInterval(poll, 1000);

    $('#clear-dtcs').click(function() {
        socket.send('clear');
    });

})
