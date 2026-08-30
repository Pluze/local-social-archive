# Publication rights and risk review

This is a conservative engineering publication review, not legal advice. It does not determine whether a particular private use is lawful and cannot guarantee compliance; laws, agreements, facts and jurisdictions differ.

## Primary sources consulted

- [Tencent WeChat Software License and Service Agreement](https://weixin.qq.com/cgi-bin/readtemplate?lang=zh_CN&t=weixin_agreement&s=default): section 7.2.4.2 says users may back up relevant service data as needed; sections 8.2.1.2, 8.2.1.4 and 8.2.1.6 restrict reverse engineering, manipulating or attaching to in-memory/runtime data, unauthorized third-party access/control, automation, and making or distributing such tools or methods; section 9 reserves software-related copyright, trademark, patent, trade-secret and other rights.
- [PRC Personal Information Protection Law — National People's Congress](http://www.npc.gov.cn/npc/c30834/202108/t20210820_313088.html): relevant when archives contain identifiable information about other people or are disclosed beyond a private household context.
- [PRC Data Security Law — National People's Congress](http://www.npc.gov.cn/npc/c30834/202106/t20210610_311888.html): relevant to secure handling, access control and risk management for collected data.
- [PRC Copyright Law — National People's Congress](http://www.npc.gov.cn/npc/c30834/202011/t20201111_308496.html) and [Regulations on Computers Software Protection — State Council](https://www.gov.cn/gongbao/content/2013/content_2339471.htm): relevant to redistribution of client binaries, copied source, protected interfaces and technical measures.

The current official administrative-regulations database states that software
ideas, processing methods and mathematical concepts are not themselves covered
by software copyright protection, while separately restricting unauthorized
copying/distribution and deliberate avoidance or destruction of copyright
technical measures. This is why the public clean-room guide documents neutral
behavior and tests but excludes operational bypass details. The Personal
Information Protection Law separately requires protection of natural persons'
personal information; its household-affairs exception is not a blanket basis
for publishing archives or tools that process other people's data.

Agreements and laws can change. Recheck the current text before publication or commercial distribution.

## Classification of the working project

| Content | Publication classification | Treatment in this repository |
|---|---|---|
| Original offline viewer, neutral schema, selective media packager | Lower risk | Included under MIT |
| Synthetic fixtures and generic path-safety tests | Lower risk | Included |
| Real conversations, contacts, identifiers, locations, media and CDN URLs | Privacy/confidentiality risk | Excluded |
| Database keys, image keys, Keychain payloads, tokens and decrypted databases | Security and privacy risk | Excluded |
| Vendor application bundle, copied assets, icons, UI screenshots and binaries | Copyright/trademark risk | Excluded |
| Third-party cloned repositories or copied snippets | License/provenance risk | Excluded; ideas reimplemented independently |
| Proprietary table layouts, binary formats and token algorithms | Contract/trade-secret/technical-measure risk | Excluded from code and operational docs |
| Process attachment, memory scanning, injection, re-signing and binary patches | High contract/security risk | Excluded; only the architectural boundary is documented |
| A tool named or branded as an official vendor product | Trademark/confusion risk | Neutral name and explicit non-affiliation used |

## Why private backup and public source are different questions

The agreement's backup language supports the user's need to preserve relevant data, but it does not grant rights to redistribute the client, other people's content, authentication material, protected implementation details, or tools prohibited elsewhere in the agreement. The public repository therefore begins at a normalized, user-authorized interchange file.

## Release checklist

- Obtain a legal review before commercial distribution or publishing a vendor adapter.
- Confirm every committed file has known authorship and license.
- Scan Git history, not just the working tree, for secrets and personal data.
- Avoid vendor names in the project name, bundle identifier, icon and screenshots.
- Do not ship a patched client, extractor binary, database key or example made from a real account.
- Require explicit consent before processing or publishing third-party communications.
