use anchor_lang::prelude::*;

declare_id!("FAjsXV6jUnBB48aydJpRXonx1jwRCbPiHTuATnTWCDiP");

#[program]
pub mod password_vault {
    use super::*;

    pub fn initialize(ctx: Context<Initialize>, data: Vec<u8>, bump: u8) -> Result<()> {
        let account = &mut ctx.accounts.storage_account;
        require!(!account.is_initialized, ErrorCode::AlreadyInitialized);
        account.is_initialized = true;
        account.data = data;
        account.bump = bump;
        Ok(())
    }
}

#[account]
pub struct StorageAccount {
    pub is_initialized: bool,
    pub data: Vec<u8>,
    pub bump: u8,
}

#[derive(Accounts)]
pub struct Initialize<'info> {
    #[account(
        init,
        payer = payer,
        space = 8 + 1 + 4 + 1024 + 1,
        seeds = [b"password_vault"],
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
}

