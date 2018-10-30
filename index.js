$(document).ready(function(w) {
    function init() {
     	mouse = {
         	x: 0,
         	y: 0,
        	px: 0,
         	py: 0,
         	down: false
     	};

     	resolution = 10;

     	canvas_width = Math.round((window.innerWidth || document.documentElement.clientWidth
                         || document.body.clientWidth)/resolution)*resolution;
     	canvas_height = Math.round((window.innerHeight || document.documentElement.clientHeight
                         || document.body.clientHeight)/resolution)*resolution;

     	pen_size = 40; //Radius around the mouse cursor coordinates to reach when stirring
     	num_cols = canvas_width / resolution; //This value is the number of columns in the grid.
     	num_rows = canvas_height / resolution; //This is number of rows.
     	speck_count = Math.pow((canvas_width + canvas_height),1.15);

     	vec_cells = []; //The array that will contain the grid cells
	    particles = []; //The array that will contain the particles


        canvas = document.getElementById("c");
        ctx = canvas.getContext("2d");

        canvas.width = canvas_width;
        canvas.height = canvas_height;

        for (i = 0; i < speck_count; i++) {
            particles.push(new particle(Math.random() * canvas_width, Math.random() * canvas_height));
        }

        for (col = 0; col < num_cols; col++) {

            vec_cells[col] = [];

            for (row = 0; row < num_rows; row++) {

                var cell_data = new cell(col * resolution, row * resolution, resolution)

                vec_cells[col][row] = cell_data;

                /*
                These two lines set the object's column and row values so the object knows
                where in the grid it is positioned.
                */
                vec_cells[col][row].col = col;
                vec_cells[col][row].row = row;

            }
        }


        for (col = 0; col < num_cols; col++) {

            for (row = 0; row < num_rows; row++) {
                var cell_data = vec_cells[col][row];
                var row_up = (row - 1 >= 0) ? row - 1 : num_rows - 1;

                var col_left = (col - 1 >= 0) ? col - 1 : num_cols - 1;
                var col_right = (col + 1 < num_cols) ? col + 1 : 0;

                var up = vec_cells[col][row_up];
                var left = vec_cells[col_left][row];
                var up_left = vec_cells[col_left][row_up];
                var up_right = vec_cells[col_right][row_up];

                cell_data.up = up;
                cell_data.left = left;
                cell_data.up_left = up_left;
                cell_data.up_right = up_right;

                up.down = vec_cells[col][row];
                left.right = vec_cells[col][row];
                up_left.down_right = vec_cells[col][row];
                up_right.down_left = vec_cells[col][row];
            }
        }

	    w.addEventListener("resize", init);
        w.addEventListener("mousedown", mouse_down_handler);
        w.addEventListener("touchstart", mouse_down_handler);

        w.addEventListener("mouseup", mouse_up_handler);
        w.addEventListener("touchend", touch_end_handler);

        canvas.addEventListener("mousemove", mouse_move_handler);
        canvas.addEventListener("touchmove", touch_move_handler);

        w.onload = draw;
    }


    function update_particle() {

        for (i = 0; i < particles.length; i++) {

            var p = particles[i];

            if (p.x >= 0 && p.x < canvas_width && p.y >= 0 && p.y < canvas_height) {

                var col = parseInt(p.x / resolution);
                var row = parseInt(p.y / resolution);

                var cell_data = vec_cells[col][row];

                var ax = (p.x % resolution) / resolution;
                var ay = (p.y % resolution) / resolution;

                p.xv += (1 - ax) * cell_data.xv * 0.05;
                p.yv += (1 - ay) * cell_data.yv * 0.05;

                p.xv += ax * cell_data.right.xv * 0.05;
                p.yv += ax * cell_data.right.yv * 0.05;

                p.xv += ay * cell_data.down.xv * 0.05;
                p.yv += ay * cell_data.down.yv * 0.05;

                p.x += p.xv;
                p.y += p.yv;

                var dx = p.px - p.x;
                var dy = p.py - p.y;

                var dist = Math.sqrt(dx * dx + dy * dy);

                var limit = Math.random() * 0.5;

                if (dist > limit) {
                    ctx.lineWidth = 1;
                    ctx.beginPath();
                    ctx.moveTo(p.x, p.y);
                    ctx.lineTo(p.px, p.py);
                    ctx.stroke();
                }else{

                    ctx.beginPath();
                    ctx.moveTo(p.x, p.y);

                    ctx.lineTo(p.x + limit, p.y + limit);

                    ctx.stroke();
                }

                p.px = p.x;
                p.py = p.y;
            }
            else {
                p.x = p.px = Math.random() * canvas_width;
                p.y = p.py = Math.random() * canvas_height;

                p.xv = 0;
                p.yv = 0;
            }

            p.xv *= 0.5;
            p.yv *= 0.5;
        }
    }

    function draw() {
        var mouse_xv = mouse.x - mouse.px;
        var mouse_yv = mouse.y - mouse.py;

        for (i = 0; i < vec_cells.length; i++) {
            var cell_datas = vec_cells[i];

            for (j = 0; j < cell_datas.length; j++) {

                var cell_data = cell_datas[j];
                random_movement(cell_data, pen_size);
                if (mouse.down) {
                    change_cell_velocity(cell_data, mouse_xv, mouse_yv, pen_size);
                }

                update_pressure(cell_data);
            }
        }

        ctx.clearRect(0, 0, canvas.width, canvas.height);

        var gradient=ctx.createLinearGradient(0,0,canvas.width,canvas.height);
        gradient.addColorStop("0","#4ed882");
        gradient.addColorStop("0.4", "#4eb5d8");
        gradient.addColorStop("0.9", "white");

        ctx.strokeStyle = gradient;

        update_particle();

        for (i = 0; i < vec_cells.length; i++) {
            var cell_datas = vec_cells[i];

            for (j = 0; j < cell_datas.length; j++) {
                var cell_data = cell_datas[j];

                update_velocity(cell_data);
            }
        }

        mouse.px = mouse.x;
        mouse.py = mouse.y;

        requestAnimationFrame(draw);
    }

    function change_cell_velocity(cell_data, mvelX, mvelY, pen_size) {
        var dx = cell_data.x - mouse.x;
        var dy = cell_data.y - mouse.y;
        var dist = Math.sqrt(dy * dy + dx * dx);

        if (dist < pen_size) {

            if (dist < 4) {
                dist = pen_size;
            }

            var power = pen_size / dist;

            cell_data.xv += mvelX * power;
            cell_data.yv += mvelY * power;
        }
    }

    function random_movement(cell_data, pen_size) {
        cell_data.xv += (Math.random()*4) - 2;
        cell_data.yv += (Math.random()*4) - 2;
    }

    function update_pressure(cell_data) {

        var pressure_x = (
            cell_data.up_left.xv * 0.5 //Divided in half because it's diagonal
            + cell_data.left.xv
            + cell_data.down_left.xv * 0.5 //Same
            - cell_data.up_right.xv * 0.5 //Same
            - cell_data.right.xv
            - cell_data.down_right.xv * 0.5 //Same
        );

        var pressure_y = (
            cell_data.up_left.yv * 0.5
            + cell_data.up.yv
            + cell_data.up_right.yv * 0.5
            - cell_data.down_left.yv * 0.5
            - cell_data.down.yv
            - cell_data.down_right.yv * 0.5
        );

        cell_data.pressure = (pressure_x + pressure_y) * 0.25;
    }

    function update_velocity(cell_data) {

        cell_data.xv += (
            cell_data.up_left.pressure * 0.5
            + cell_data.left.pressure
            + cell_data.down_left.pressure * 0.5
            - cell_data.up_right.pressure * 0.5
            - cell_data.right.pressure
            - cell_data.down_right.pressure * 0.5
        ) * 0.25;

        cell_data.yv += (
            cell_data.up_left.pressure * 0.5
            + cell_data.up.pressure
            + cell_data.up_right.pressure * 0.5
            - cell_data.down_left.pressure * 0.5
            - cell_data.down.pressure
            - cell_data.down_right.pressure * 0.5
        ) * 0.25;

        cell_data.xv *= 0.99;
        cell_data.yv *= 0.99;
    }


    function cell(x, y, res) {

        this.x = x;
        this.y = y;

        this.r = res;

        this.col = 0;
        this.row = 0;

        this.xv = 0;
        this.yv = 0;

        this.pressure = 0;

    }

    function particle(x, y) {
        this.x = this.px = x;
        this.y = this.py = y;
        this.xv = this.yv = 0;
    }


    function mouse_down_handler(e) {
        jQuery(".drag-me").fadeOut(1500);
        e.preventDefault(); //Prevents the default action from happening (e.g. navigation)
        mouse.down = true; //Sets the mouse object's "down" value to true
    }

    function mouse_up_handler() {
        mouse.down = false;
    }

    function touch_end_handler(e) {
        if (!e.touches) mouse.down = false; //If there are no more touches on the screen, sets "down" to false.
    }

    function mouse_move_handler(e) {
        mouse.px = mouse.x;
        mouse.py = mouse.y;

        var rect = canvas.getBoundingClientRect(),
            scaleX = canvas.width / rect.width,
            scaleY = canvas.height / rect.height;

        mouse.x = (e.clientX - rect.left) * scaleX;
        mouse.y = (e.clientY - rect.top) * scaleY;
    }

    function touch_move_handler(e) {
        mouse.px = mouse.x;
        mouse.py = mouse.y;

        var rect = canvas.getBoundingClientRect(),
            scaleX = canvas.width / rect.width,
            scaleY = canvas.height / rect.height;

        mouse.x = (e.touches[0].pageX - rect.left) * scaleX;
        mouse.y = (e.touches[0].pageY - rect.top) * scaleY;
    }

    w.Fluid = {
        initialize: init
    }

}(window)); //Passes "window" into the self-invoking function.

window.requestAnimationFrame = window.requestAnimationFrame || window.webkitRequestAnimationFrame || window.mozRequestAnimationFrame;

Fluid.initialize();
