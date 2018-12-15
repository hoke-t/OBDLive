$(document).ready(function () {

    var socket = new WebSocket('ws://' + window.location.host);
    var pid_map = {
        '1': 'engine-rpm',
        '2': 'vehicle-speed',
        '3': 'throttle-position',
        '4': 'engine-oil-temperature',
        '5': 'ethanol-fuel-percent',
        '6': 'maf-air-flow-rate',
        '7': 'run-time-since-engine-start',
        '8': 'engine-fuel-rate',
        '9': 'ambient-air-temperature',
        '10': 'engine-load',
    };

    function poll () {
        socket.send(JSON.stringify({
            "pids": ["1", "2", "3", "4", "6", "7", "10"]
        }));
    };

    socket.onopen = function open() {
        console.log('WebSockets connection created.');
    };

    var throttle_position_rp = radialProgress(document.getElementById('throttle-position'))
        .label("Throttle Position")
        .diameter(250)
        .value(10)
        .render();
    
    var engine_load_rp = radialProgress(document.getElementById('engine-load'))
        .label("Engine Load")
        .diameter(250)
        .value(10)
        .render();
   
    var speedometer = new Gauge("vehicle-speed", {size: 300, label: "Speed", min: 0, max: 150, minorTicks: 5})
    speedometer.render();

    var rpm_gauge = new Gauge("engine-rpm", {size: 300, label: "RPM", min: 0, max: 8000,     minorTicks: 5})
    rpm_gauge.render();

    var engine_oil_temp_gauge = new Gauge("engine-oil-temp", {size: 300, label: "Engine Oil", min: 0, max: 150, minorTicks: 5});
    engine_oil_temp_gauge.render();

    socket.onmessage = function message(event) {
        pid_data = JSON.parse(event.data)['data'];

        for (var pid in pid_data) {
            if (!pid_data.hasOwnProperty(pid))
                continue;
            console.log(pid_map[pid] + " = " + pid_data[pid]);
            if (pid_map[pid] == 'throttle-position') {
                throttle_position_rp.value(pid_data[pid]).render();
            } else if (pid_map[pid] == 'engine-load') {
                engine_load_rp.value(pid_data[pid]).render();
            } else if (pid_map[pid] == 'vehicle-speed') {
                speedometer.redraw(pid_data[pid]);
            } else if (pid_map[pid] == 'engine-rpm') {
                rpm_gauge.redraw(pid_data[pid]);
            } else if (pid_map[pid] == 'engine-oil-temperature') {
               engine_oil_temp_gauge.redraw(pid_data[pid]); 
            } else {
                document.getElementById(pid_map[pid]).innerText = pid_data[pid];
            }
        }
    };

    if (socket.readyState == WebSocket.OPEN) {
        socket.onopen();
    }

    window.setInterval(poll, 200);

})
