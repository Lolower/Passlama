use anchor_lang::prelude::*;

declare_id!("GCA4aqiUT57vPoc6seLrSLBXk9BRnp3Ptpqb6nbg19JH");

#[program]
pub mod password_vault {
    use super::*;

    pub fn initialize(ctx: Context<Initialize>, data: Vec<u8>, bump: u8) -> Result<()> {
        let account = &mut ctx.accounts.storage_account;
        require!(!account.is_initialized, ErrorCode::AlreadyInitialized);
        require!(data.len() <= 2048, ErrorCode::DataTooLarge);
        account.is_initialized = true;
        account.data[..data.len()].copy_from_slice(&data);
        account.data_len = data.len() as u32;
        account.bump = bump;
        Ok(())
    }
}

#[account]
pub struct StorageAccount {
    pub is_initialized: bool,
    pub data: [u8; 2048],
    pub data_len: u32,
    pub bump: u8,
}

#[derive(Accounts)]
#[instruction(bump: u8)]
pub struct Initialize<'info> {
    #[account(
        init,
        payer = payer,
        space = 8 + 1 + 2048 + 4 + 1,
        seeds = [payer.key().as_ref(), b"password_vault"],
        bump
    )]
    pub storage_account: Account<'info, StorageAccount>,
    #[account(mut)]
    pub payer: Signer<'info>,
    pub system_program: Program<'info, System>,
}

#[error_code]
pub enum ErrorCode {
    #[msg("Account already initialized")]
    AlreadyInitialized,
    #[msg("Data size exceeds maximum allowed")]
    DataTooLarge,
}
