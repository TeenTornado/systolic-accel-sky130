`timescale 1ns/1ps
module pe #(
    parameter PIPE_STAGES = 0
) (
    input  wire               clk,
    input  wire               rst_n,
    input  wire               w_load,
    input  wire signed [7:0]  w_in,
    input  wire signed [7:0]  a_in,
    input  wire signed [31:0] psum_in,
    output reg  signed [7:0]  a_out,
    output reg  signed [31:0] psum_out
);
    reg signed [7:0] w_reg;
    wire signed [15:0] prod_comb = a_in * w_reg;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            w_reg <= 8'sd0;
        end else if (w_load) begin
            w_reg <= w_in;
        end
    end

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            a_out <= 8'sd0;
        end else begin
            a_out <= a_in;
        end
    end

    generate
        if (PIPE_STAGES == 0) begin : g_nopipe
            always @(posedge clk or negedge rst_n) begin
                if (!rst_n) begin
                    psum_out <= 32'sd0;
                end else begin
                    psum_out <= psum_in + {{16{prod_comb[15]}}, prod_comb};
                end
            end
        end else begin : g_pipe
            reg signed [15:0] prod_reg;
            always @(posedge clk or negedge rst_n) begin
                if (!rst_n) begin
                    prod_reg <= 16'sd0;
                    psum_out <= 32'sd0;
                end else begin
                    prod_reg <= prod_comb;
                    psum_out <= psum_in + {{16{prod_reg[15]}}, prod_reg};
                end
            end
        end
    endgenerate
endmodule
