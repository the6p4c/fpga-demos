module top(
	input CLK,

	output PIN_6,
	output PIN_7,
	output PIN_8,
	output PIN_9,
	output PIN_10,
	output PIN_11,
	output PIN_12,
	output PIN_13,

	output PIN_16,
	output PIN_15
);
	reg rst = 1;
	reg [10:0] rst_cnt = 0;
	always @(posedge CLK) begin
		if (rst_cnt == 20) begin
			rst <= 0;
		end else begin
			rst_cnt <= rst_cnt + 1;
		end
	end

	cpu cpu_inst(
		.clk(CLK),
		.rst(rst),
		.r_win(0),
		.db({PIN_6, PIN_7, PIN_8, PIN_9, PIN_10, PIN_11, PIN_12, PIN_13}),
		.rs(PIN_16),
		.e(PIN_15)
	);
endmodule
