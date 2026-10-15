`timescale 1ns/1ps
module systolic_array #(
    parameter N           = 4,
    parameter PIPE_STAGES = 0
) (
    input  wire                 clk,
    input  wire                 rst_n,
    input  wire                 w_load,
    input  wire [N*N*8-1:0]     w_flat,
    input  wire [N*8-1:0]       a_row,
    output wire [N*32-1:0]      c_col
);
    wire signed [7:0]  a_wire [0:N-1][0:N];
    wire signed [31:0] p_wire [0:N][0:N-1];

    genvar i;
    genvar j;
    generate
        for (i = 0; i < N; i = i + 1) begin : g_row_in
            assign a_wire[i][0] = a_row[i*8 +: 8];
        end
        for (j = 0; j < N; j = j + 1) begin : g_col_io
            assign p_wire[0][j] = 32'sd0;
            assign c_col[j*32 +: 32] = p_wire[N][j];
        end
        for (i = 0; i < N; i = i + 1) begin : g_r
            for (j = 0; j < N; j = j + 1) begin : g_c
                pe #(.PIPE_STAGES(PIPE_STAGES)) u_pe (
                    .clk      (clk),
                    .rst_n    (rst_n),
                    .w_load   (w_load),
                    .w_in     (w_flat[(i*N + j)*8 +: 8]),
                    .a_in     (a_wire[i][j]),
                    .psum_in  (p_wire[i][j]),
                    .a_out    (a_wire[i][j+1]),
                    .psum_out (p_wire[i+1][j])
                );
            end
        end
    endgenerate
endmodule
